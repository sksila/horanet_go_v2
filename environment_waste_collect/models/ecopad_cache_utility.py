import logging

from odoo import fields, models, api
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class EcopadCacheUtility(models.AbstractModel):
    u"""Modèle de gestion de certaines méthodes de l'API Ecopad, afin d'optimiser les temps de réponse."""

    # region Private attributes
    _name = 'horanet.environment.ecopad.cache.utility'

    # endregion

    # region Default methods

    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods

    # region partner
    def _get_file_cache_environment_partner(self):
        u"""Cherche le record ir.attachment de stockage du cache des données partner."""
        return self.env.ref('environment_waste_collect.ecopad_get_partner_cached_data_file',
                            raise_if_not_found=True)

    @api.multi
    def get_partner_cached_data(self):
        u"""Récupère une liste des données partner, stocké en cache."""
        result = (None, None)
        file_cache_environment_partner = self._get_file_cache_environment_partner()
        if file_cache_environment_partner and file_cache_environment_partner.datas:
            result = (
                self._read_file_data(file_cache_environment_partner.datas),
                file_cache_environment_partner.write_date)
        return result

    @api.multi
    def _update_environment_partner_file(self):
        u"""Met à jour les données du cache des forfait dans un fichier."""
        file_cache_environment_partner = self._get_file_cache_environment_partner()
        partner_data, search_date = self.get_environment_partner_data()
        file_cache_environment_partner.write({
            'datas': self._prepare_file_data(partner_data),
            'write_date': search_date
        })

    @api.multi
    def get_environment_partner_data(self, date_limit=False):
        u"""Recherche les données des partner à synchroniser avec un Ecopad.

        Cette méthode sert à l'API de récupération des données Ecopad

        :param date_limit: si fourni, la date à partir de laquelle les données doivent être récupérées (différentiel)
        si non fourni, toutes les données sont recherchés (long)
        :return: (partner_data <list(dict())>, date_effective <str-datetime>)
        """
        id_guardian_cat = self.env.ref('environment_waste_collect.environment_category_guardian').id

        partner_domain = [('has_active_environment_subscription', '=', True)]
        if date_limit:
            partner_domain.append(('write_date', '>', date_limit))

        search_date = fields.Datetime.now()
        all_partners = self.env['res.partner'].search_read(partner_domain,
                                                           fields=[
                                                               'name',
                                                               'better_contact_address',
                                                               'write_date',
                                                               'subscription_category_ids',
                                                               'is_company'])
        list_data_partner = []
        _logger.info("Generate partner cached data for #{number} partner".format(number=str(len(all_partners))))

        chunk_size = 100
        for partners in [all_partners[i * chunk_size:(i + 1) * chunk_size]
                         for i in range((len(all_partners) + chunk_size - 1))]:
            list_data_partner.extend([{
                'id': partner['id'],
                'name': partner['name'],
                'better_contact_address': partner['better_contact_address'],
                'write_date': partner['write_date'],
                'partner_category_ids': partner['subscription_category_ids'],
                'is_company': partner['is_company'],
                'is_guardian': id_guardian_cat in partner['subscription_category_ids']
            } for partner in partners])

        return list_data_partner, search_date

    # endregion
    # region packages

    def _get_file_cache_environment_packages(self):
        u"""Cherche le record ir.attachment de stockage du cache des données de forfait."""
        return self.env.ref('environment_waste_collect.ecopad_get_contract_cached_data_file',
                            raise_if_not_found=True)

    @api.multi
    def get_contract_cached_data(self):
        u"""Récupère une liste des données de forfait, stocké en cache."""
        result = (None, None)
        file_cache_environment_packages = self._get_file_cache_environment_packages()
        if file_cache_environment_packages and file_cache_environment_packages.datas:
            result = (
                self._read_file_data(file_cache_environment_packages.datas),
                file_cache_environment_packages.write_date)
        return result

    @api.multi
    def _update_environment_package_file(self):
        u"""Met à jour les données du cache des forfait dans un fichier."""
        file_cache_environment_packages = self._get_file_cache_environment_packages()
        contract_data, search_date = self.get_environment_package_data()
        file_cache_environment_packages.write({
            'datas': self._prepare_file_data(contract_data),
            'write_date': search_date
        })

    @api.multi
    def get_environment_package_data(self, date_limit=False):
        u"""Recherche les données des contrats à synchroniser avec un Ecopad.

        Cette méthode sert à l'API de récupération des données Ecopad

        :param date_limit: si fourni, la date à partir de laquelle les données doivent être récupérées (différentiel)
        si non fourni, toutes les données sont recherchés (long)
        :return: (contract_data <list(dict())>, date_effective <str-datetime>)
        """
        domain_subscription = [
            ('application_type', '=', 'environment'),
            ('state', '=', 'active')
        ]

        ids_environment_subscription = self.env['horanet.subscription'].search(
            domain_subscription).with_context(prefetch_fields=False).ids

        package_line_model = self.env['horanet.package.line']
        domain_package = [('subscription_id', 'in', ids_environment_subscription)]
        if date_limit:
            domain_package.append(('write_date', '>=', date_limit))
        search_date = fields.Datetime.now()

        filter_action_ids = self.env['horanet.action'].search([('code', 'in', ['ACCESS', 'PASS', 'DEPOT'])]).ids
        filter_activities = self.env['horanet.activity'].search([('default_action_id', 'in', filter_action_ids)]).ids

        all_package_lines = package_line_model.search(domain_package + [('activity_ids', 'in', filter_activities)])
        package_data = []

        chunk_size = 1000
        current = 0
        while current < len(all_package_lines):
            package_line_chunk = all_package_lines[current:current + chunk_size]

            _logger.info("Get packages data, chunk {current}/{total}".format(
                current=str(current) + '-' + str(current + len(package_line_chunk)),
                total=str(len(all_package_lines))))
            current += chunk_size

            package_data.extend([{
                'id': package_line.id,
                'starting_date': package_line.opening_date,
                'ending_date': package_line.closing_date,
                'write_date': package_line.write_date,
                'state': package_line.state,
                'is_derogation': package_line.is_derogation,
                'balance_remaining': package_line.balance_remaining,
                'partner_id': package_line.recipient_id.id,
                'action_code':
                    package_line.activity_ids[0].default_action_id.code
                    if package_line.activity_ids and package_line.activity_ids[0].default_action_id else False,
                'activity_ids': package_line.activity_ids.ids,
            } for package_line in package_line_chunk])

        return package_data, search_date

    # endregion
    # region tags
    def _get_file_cache_environment_tags(self):
        u"""Cherche le record ir.attachment de stockage du cache des données de tag."""
        return self.env.ref('environment_waste_collect.ecopad_get_tag_cached_data_file', raise_if_not_found=True)

    @api.multi
    def get_tag_cached_data(self):
        u"""Récupère une liste des données tag, stocké en cache."""
        result = (None, None)
        file_cache_environment_tag = self._get_file_cache_environment_tags()
        if file_cache_environment_tag and file_cache_environment_tag.datas:
            result = (
                self._read_file_data(file_cache_environment_tag.datas),
                file_cache_environment_tag.write_date)
        return result

    @api.multi
    def _update_environment_tag_file(self):
        u"""Met à jour les données du cache des tags dans un fichier."""
        file_cache_environment_tag = self._get_file_cache_environment_tags()
        tag_data, search_date = self.get_environment_tag_data()
        file_cache_environment_tag.write({
            'datas': self._prepare_file_data(tag_data),
            'write_date': search_date
        })

    @api.multi
    def get_environment_tag_data(self, date_limit=False, partner_id=False, only_guardian=False):
        """Return for the Ecopad API all the tag assigned to a partner having an environment contract (active).

        :param partner_id: a partner id (int), optional, used to get only one partner tags
        :param date_limit: limit the search to the assignations write_date > last_sync_date
        :return: list of dict({
            'id': Int
            'active': Boolean
            'number': String
            'external_reference': String
            'partner_id': Int
            'is_guardian': Boolean
        """
        partner_search_domain = [('has_active_environment_subscription', '=', True)]
        if partner_id:
            partner_search_domain = partner_search_domain + [('id', '=', partner_id)]

        id_guardian_cate = self.env.ref('environment_waste_collect.environment_category_guardian').id
        if only_guardian:
            partner_search_domain = partner_search_domain + [('subscription_category_ids', 'in', id_guardian_cate)]
        else:
            partner_search_domain = partner_search_domain + [('subscription_category_ids', 'not in', id_guardian_cate)]

        partners = self.env['res.partner'].search(partner_search_domain)
        search_assignation_partner_domain = [
            '&',
            '&',
            ('reference_id', '!=', False),
            ('reference_id', '=like', 'res.partner%'),
            ('partner_id', 'in', partners.ids)
        ]
        search_date = fields.Datetime.now()

        assignation_model = self.env['partner.contact.identification.assignation']
        search_assignations_by_date_domain = []
        if date_limit:
            search_assignations_by_date_domain = expression.OR([
                [('write_date', '>', fields.Datetime.to_string(date_limit))],
                # Rechercher aussi les assignations qui ne seraient plus actives depuis la dernière synchronisation
                expression.AND([
                    assignation_model.search_is_active(operator='=', value=True, search_date=date_limit),
                    assignation_model.search_is_active(operator='=', value=False, search_date=fields.Datetime.now())
                ]),
                # Rechercher aussi les assignations qui ne seraient devenues actives depuis la dernière synchronisation
                expression.AND([
                    assignation_model.search_is_active(operator='=', value=False, search_date=date_limit),
                    assignation_model.search_is_active(operator='=', value=True, search_date=fields.Datetime.now())
                ])
            ])
        search_assignation_domain = expression.AND([
            search_assignation_partner_domain,
            search_assignations_by_date_domain])

        # Recherche en SQL pour éviter de calculer les champs name des partner et tag (on as juste besoin de leurs id)
        # Objectif, améliorer les performances
        assignation_ids = self.env['partner.contact.identification.assignation'].search(
            search_assignation_domain).ids
        assignation_select = []
        if assignation_ids:
            self.env.cr.execute("SELECT partner_id, tag_id from partner_contact_identification_assignation "
                                "where id in %s",
                                [tuple(assignation_ids)])
            assignation_select = self.env.cr.fetchall()

        partner_id_by_tag_id = {select[1]: select[0] for select in assignation_select}
        tag_to_search_ids = [select[1] for select in assignation_select]

        search_tag_domain = expression.AND([
            [('id', 'in', tag_to_search_ids)],
            self.get_environment_tags_search_domain(None)])

        all_tags = self.env['partner.contact.identification.tag'].search(search_tag_domain)

        _logger.info("Generate tag cached data for #{number} tags".format(number=str(len(all_tags))))

        tag_data = []
        tag_data.extend([{
            'id': tag.id,
            'active': tag.active,
            'number': tag.number,
            'external_reference': tag.external_reference,
            'partner_id': partner_id_by_tag_id.get(tag.id, None),
            } for tag in all_tags])

        return tag_data, search_date

    @api.model
    def get_environment_tags_search_domain(self, search_tag_domain):
        """Placeholder for an eventual override of the tag research for the Environment API."""
        return search_tag_domain

    # endregion
    @staticmethod
    def _prepare_file_data(data):
        """Utility method to dump / encode and zip data."""
        import json
        from io import BytesIO
        import gzip

        json_data = json.dumps(data)
        gzip_buffer = BytesIO()
        gzip_file = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=gzip_buffer)
        gzip_file.write(json_data)
        gzip_file.close()

        encoded_data = gzip_buffer.getvalue().encode('base64')

        return encoded_data

    @staticmethod
    def _read_file_data(data):
        """Utility method to load / decode and unzip data."""
        from io import BytesIO
        import gzip
        import json

        decoded_data = data.decode('base64')

        gzip_buffer = BytesIO(decoded_data)
        gzip_file = gzip.GzipFile(mode='rwb', compresslevel=6, fileobj=gzip_buffer)
        unzipped_data = gzip_file.read()
        gzip_file.close()

        return json.loads(unzipped_data)

    @api.model
    def _cron_ecopad_synchronization_cache_file(self):
        """Entry point of CRON Ecopad cache file.

        Prepare or update cache file for the current date
        """
        import time
        _logger.info(u"Start CRON Ecopad synchronization cached files")

        start_time = time.time()
        self._update_environment_partner_file()
        _logger.info(u"Cron engine : done generating partner cache file (runtime: {exec_time:0.3f}s)".format(
            exec_time=round(time.time() - start_time, 3)))

        start_time = time.time()
        self._update_environment_package_file()
        _logger.info(u"Cron engine : done generating contract cache file (runtime: {exec_time:0.3f}s)".format(
            exec_time=round(time.time() - start_time, 3)))

        start_time = time.time()
        self._update_environment_tag_file()
        _logger.info(u"Cron engine : done generating tags cache file (runtime: {exec_time:0.3f}s)".format(
            exec_time=round(time.time() - start_time, 3)))

        _logger.info(u"End CRON Ecopad synchronization cached files")

    # endregion

    pass
