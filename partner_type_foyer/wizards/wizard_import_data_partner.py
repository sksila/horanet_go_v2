from io import BytesIO
import base64
import logging
import os
import shutil
import tempfile
import zipfile

# 2 :  imports of openerp
from odoo import _, api, exceptions, fields, models
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)

PARTNER_FIELD = ['external_id',
                 'country_code',
                 'country_state_extid',
                 'city_code',
                 'street_code',
                 'zip_code',
                 'title_extid',
                 'street_number_code',
                 'firstname',
                 'lastname',
                 'email',
                 'phone',
                 'mobile',
                 'birthdate_date']

RELATION_FIELD = ['partner_ext_id',
                  'foyer_ext_id',
                  'is_responsible',
                  'begin_date',
                  'end_date']

IMPORT_METHOD = (('orm', 'Using ORM'), ('sql', 'By SQL (experimental)'))


class ResetAndImportDataFr(models.TransientModel):
    """Allow import of res.partner from a data file.

    Usage can be done via the ORM or via SQL for better perfs on large dataset.
    """

    # region Private attributes
    _name = 'horanet.citizen.wizard.import.partner'
    _description = 'Import data location '
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    conserve_uploaded_file = fields.Boolean(string="Conserve uploaded file", default=False,
                                            help="Uploaded archive content is save on the server in a temporary"
                                                 " directory, if set to true, the folder will be conserved after the"
                                                 " import, otherwise it will be regarding of the"
                                                 " import result. (consult the log for the path)")
    import_method = fields.Selection(string="Choose import method", selection=IMPORT_METHOD, default='orm')
    track_history = fields.Boolean(string="Track history during import", default=False)
    module_name = fields.Char(string="Module name for external id", default='partner_type_foyer')
    datafile = fields.Binary(string="Compressed file containing data")
    datafile_file_name = fields.Char(string="hidden file name")
    delete_all_before_import = fields.Boolean(string="Delete all previous external id", default=False)

    # endregion

    @api.multi
    def run_import(self):
        """Start the process of import if everything seems valid.

        :raise: openerp.exceptions.Warning if file isn't provided
        :raise: openerp.exceptions.Warning if module name isn't valid
        """
        self.ensure_one()
        # test value cohérence
        if not self.datafile and self.delete_all_before_import:
            return self._delete_all_previous_external_id()
        if not self.datafile:
            raise exceptions.Warning(_('The data file is mandatory'))
        if not self.module_name or len(self.module_name) < 5:
            raise exceptions.Warning(_('The module name seems to be invalide (< 5 char)'))
        _logger.info('Start Import, this operation take time')
        _logger.info('Data file conversion and extraction')
        temp_dir = tempfile.mkdtemp(prefix='odoo_horanet_tmp_')
        try:
            _logger.warning(u'création du dossier :' + str(temp_dir))
            test = BytesIO(base64.decodestring(self.datafile))
            pyzip = zipfile.ZipFile(test)
            pyzip.extractall(temp_dir)
            _logger.info('Data file conversion and extraction, DONE')

            required_data = dict()
            required_data['partner.csv'] = PARTNER_FIELD
            required_data['relation_foyer.csv'] = RELATION_FIELD
            dictionary_file = self._check_and_get_data_file(required_data, temp_dir)

            self._start_sql_import(dictionary_file)
            _logger.info('Congratulation Import done')
        finally:
            if not self.conserve_uploaded_file:
                shutil.rmtree(temp_dir)
        return True

    @api.multi
    def _start_sql_import(self, dictionary_file):
        """Launch the import."""
        self.ensure_one()

        _logger.info('Start SQL Import')
        cr = self.env.cr

        if self.delete_all_before_import:
            self._delete_all_previous_external_id()
        else:
            _logger.info('Deletion of previous external id record ignored')

        _logger.info('Get partner data')
        data_partner = self._get_data_csv(dictionary_file['partner.csv'])

        self = self.with_context({'tracking_disable': not self.track_history})

        # Expecting list_data_city : ('name', 'code', 'zip_ids', 'country_state_id')
        _logger.info('Start Partner import, ' + str(len(data_partner)) + ' records')

        # We get the dictionary with all the data
        data_partner_sanitized = self._get_partners_dictionary(data_partner)

        # Then we create the partners
        map_ext_id_partner_id = self._import_create_partners(data_partner_sanitized)

        _logger.info(str(len(map_ext_id_partner_id)) + ' Partner created')

        _logger.info('Start creation external id')
        self._create_external_id(map_ext_id_partner_id, 'res.partner')
        _logger.info(str(len(map_ext_id_partner_id)) + ' External id created')

        _logger.info('Get relation data')
        data_relation = self._get_data_csv(dictionary_file['relation_foyer.csv'])
        if len(data_relation) > 0:
            # Then we create the relations
            data_relation_sanitized = self._import_partner_relations(map_ext_id_partner_id, data_relation)

            _logger.info('Import relation complete ' + str(len(data_relation_sanitized)))
        else:
            _logger.info('No relations to import')

        cr.commit()

    # region UTILS
    @api.multi
    def _delete_all_previous_external_id(self):
        """Delete external ids of partners generated by this module.

        Avoid import error because of existing data
        """
        cr = self.env.cr
        _logger.info('Delete all previous external id')
        cr.execute(
            "delete from ir_model_data where module = '" + str(
                self.module_name) + "' and model = 'res.partner'")
        cr.commit()
        _logger.info('Delete complete')

    def _construct_partner_dictionary(self, partner, list_country_id, list_state_id, list_city_id, list_city_name,
                                      list_zip_id, list_zip_name, list_street_number_id, list_title_id):
        """
        Construct the dictionary of the corresponding partner with its data.

        :param partner: the partner
        :return: the partner data and its external id
        """
        country_france_rec_id = self.env.ref('base.fr').id

        partner['country_id'] = list_country_id.get(partner.pop('country_code'))
        partner['state_id'] = list_state_id.get(partner.pop('country_state_extid'))
        partner['city_id'] = list_city_id.get(partner.pop('city_code'))

        if partner.get('city_id', False):
            partner['city'] = list_city_name.get(partner['city_id'], '')

        partner['street_id'] = None

        if partner.get('street_code', False):
            if partner.get('city_id', False):
                street_rec = self.env['res.street'].sudo().search_read(
                    [('code', '=', partner.get('street_code')),
                     ('city_id', '=', partner['city_id'])],
                    ['name'])
                if street_rec and len(street_rec) == 1:
                    partner['street_id'] = street_rec[0]['id']
                    partner['street'] = str(partner.get('street_number_code', '')) + ' ' + str(
                        street_rec[0]['name'])
        partner.pop('street_code')

        partner['zip_id'] = list_zip_id.get(partner.pop('zip_code'))
        if partner.get('zip_id', False):
            partner['zip'] = str(list_zip_name.get(partner['zip_id']))

        partner['street_number_id'] = list_street_number_id.get(partner.pop('street_number_code'))
        partner['title'] = list_title_id.get(partner.pop('title_extid'))
        partner['notify_email'] = partner.get('notify_email', 'none')
        partner['birthdate_date'] = fields.Date.from_string(partner.get('birthdate_date', False))

        if not partner.get('name', False):
            if partner.get('company_type', 'person') == 'foyer':
                partner['name'] = 'Foyer'
            else:
                partner['name'] = " ".join((p for p in (partner['lastname'], partner['firstname']) if p))

        partner['address_status'] = 'confirmed'

        # Les foyers doivent être en is_company True
        partner['is_company'] = False if partner.get('company_type', 'person') == 'person' else True

        # On rajoute certaines données car dans ce mode elles ne sont pas auto-calculées
        if self.import_method == 'sql':
            partner['customer'] = partner.get('customer', True)
            partner['active'] = partner.get('active', True)
            partner['is_company'] = partner.get('is_company', False)
            partner['employee'] = partner.get('employee', False)
            partner['type'] = partner.get('type', 'contact')
            partner['company_type'] = partner.get('company_type', 'person')
            partner['display_name'] = partner.get('name', 'None')
            if partner['company_type'] == 'default' and partner['country_id'] == country_france_rec_id:
                if not partner.get('state_id', False) or not partner.get('city_id', False) or not partner.get(
                        'zip_id', False) or not partner.get('street_id', False):
                    partner['address_status'] = 'incomplete'
            if partner['company_type'] == 'foyer':
                partner['is_company'] = True

        ext_id = partner.pop('external_id')

        return partner, ext_id

    def _get_partners_dictionary(self, data_partner):
        """
        Get the dictionary with all the partners and their data.

        :param data_partner:
        :return:
        """
        # country_code
        _logger.info('Get country records')
        list_country_code = list(set([x['country_code'] for x in data_partner]))
        list_country_rec = self.env['res.country'].sudo().search_read([('code', 'in', list_country_code)], ['code'])
        list_country_id = {c['code']: c['id'] for c in list_country_rec}

        # country_state_extid
        _logger.info('Get state records')
        list_state_extid = list(set([x['country_state_extid'] for x in data_partner]))
        list_state_extid_rec = self.env['ir.model.data'].sudo().search_read(
            [('model', '=', 'res.country.state'), ('name', 'in', list_state_extid)], ['res_id', 'name'])
        list_state_id = {s['name']: s['res_id'] for s in list_state_extid_rec}

        # city_code
        _logger.info('Get city records')
        list_city_code = list(set([x['city_code'] for x in data_partner]))
        list_city_rec = self.env['res.city'].sudo().search_read([('code', 'in', list_city_code)], ['code', 'name'])
        list_city_id = {c['code']: c['id'] for c in list_city_rec}
        list_city_name = {c['id']: c['name'] for c in list_city_rec}

        # zip_code
        _logger.info('Get zip records')
        list_zip_name = list(set([x['zip_code'] for x in data_partner]))
        list_zip_rec = self.env['res.zip'].sudo().search_read([('name', 'in', list_zip_name)], ['name'])
        list_zip_id = {c['name']: c['id'] for c in list_zip_rec}
        list_zip_name = {c['id']: c['name'] for c in list_zip_rec}

        # title_extid
        _logger.info('Get title records')
        list_title_extid = list(set([x['title_extid'] for x in data_partner]))
        list_title_rec = self.env['ir.model.data'].sudo().search_read(
            [('model', '=', 'res.partner.title'), ('name', 'in', list_title_extid)], ['res_id', 'name'])
        list_title_id = {s['name']: s['res_id'] for s in list_title_rec}

        # street_number_code
        _logger.info('Get street number records')
        list_street_number_name = list(set([x['street_number_code'] for x in data_partner]))
        list_street_number_rec = self.env['res.street.number'].sudo().search_read(
            [('name', 'in', list_street_number_name)], ['name'])
        list_street_number_id = {s['name']: s['id'] for s in list_street_number_rec}

        _logger.info('Start creating partner (%s)' % (str(len(data_partner))))

        # Conversion des fields avec leurs id correspondant
        _logger.info(u'Conversion et ajout de données partner')

        data_partner_sanitized = []
        for partner in data_partner:
            partner, ext_id = self._construct_partner_dictionary(partner, list_country_id, list_state_id, list_city_id,
                                                                 list_city_name, list_zip_id, list_zip_name,
                                                                 list_street_number_id, list_title_id)

            data_partner_sanitized.append((partner, ext_id))

        return data_partner_sanitized

    def _import_create_partners(self, data_partner_sanitized):
        """
        Create all the partners.

        :param data_partner_sanitized: partners with their data
        :return: external id of created partners
        """
        loop_number = 0
        res_partner = self.env['res.partner']
        map_ext_id_partner_id = []
        cr = self.env.cr

        if self.import_method == 'orm':
            for partner, ext_id in data_partner_sanitized:
                loop_number += 1
                if loop_number % 10 == 0:
                    _logger.info('Creating partner %s' % loop_number)
                map_ext_id_partner_id.append((res_partner.create(partner)[0].id, ext_id))
        else:
            static_values = str(self.env.uid) + ", CURRENT_TIMESTAMP, " + str(self.env.uid) + ", CURRENT_TIMESTAMP"
            static_fields = "create_uid, create_date, write_uid, write_date"
            insert_fields = [k for (k, v) in data_partner_sanitized[0][0].items()]

            insert_queries = []
            for partner, ext_id in data_partner_sanitized:
                vals = [partner[idx] for idx in insert_fields]
                insert_queries.append(cr.mogrify("(" + static_values + ", %s" * len(vals) + ')', tuple(vals)))
            cr.execute(
                'INSERT INTO res_partner(' + static_fields + ',' + ','.join(insert_fields) + ') VALUES' + ','.join(
                    insert_queries) + (' RETURNING id' if True else ''))

            ext_id_to_create = cr.fetchall()
            map_ext_id_partner_id = zip([x[0] for x in ext_id_to_create], [x[1] for x in data_partner_sanitized])

        return map_ext_id_partner_id

    def _import_partner_relations(self, map_ext_id_partner_id, data_relation):
        """
        Create relations between partners and foyers.

        :param map_ext_id_partner_id: external ids of partners
        :param data_relation: data of partners relations
        :return: list of partners created
        """
        dictionary_partner_ids = dict([(ext_id, id_tech) for id_tech, ext_id in map_ext_id_partner_id])

        data_relation_sanitized = []
        loop_number = 0
        cr = self.env.cr

        for relation in data_relation:
            # récupération de l'identifiant partner dans le fichier
            partner_ext_id = relation.pop('partner_ext_id')
            relation['partner_id'] = dictionary_partner_ids.get(partner_ext_id)
            # recherche des identifiants du partner dans la base de données
            if not relation.get('partner_id', False):
                partner_rec = self.env['ir.model.data'].sudo().search_read(
                    [('model', '=', 'res.partner'), ('name', '=', partner_ext_id)], ['res_id'])
                if partner_rec and len(partner_rec) == 1:
                    relation['partner_id'] = partner_rec[0]['res_id']
                if not relation.get('partner_id', False):
                    _logger.info(u'Pas de partner retrouvé pour ' + partner_ext_id)
                    raise Exception('Pas de partner retrouvé pour ' + partner_ext_id)

            # récupération de l'identifiant partner dans le fichier
            foyer_id_ext = relation.pop('foyer_ext_id')
            relation['foyer_id'] = dictionary_partner_ids.get(foyer_id_ext)
            # recherche des identifiants du partner dans la base de données
            if not relation.get('foyer_id', False):
                partner_foyer_rec = self.env['ir.model.data'].sudo().search_read(
                    [('model', '=', 'res.partner'), ('name', '=', foyer_id_ext)], ['res_id'])
                if partner_foyer_rec and len(partner_foyer_rec) == 1:
                    relation['foyer_id'] = partner_foyer_rec[0]['res_id']
                if not relation.get('foyer_id', False):
                    _logger.info('Pas de foyer retrouvé pour ' + foyer_id_ext)
                    raise Exception('Pas de foyer retrouvé pour ' + foyer_id_ext)
            # récupération dans le fichier
            relation['begin_date'] = fields.Date.from_string(relation.get('begin_date', False))
            relation['end_date'] = fields.Date.from_string(relation.get('end_date', False))
            relation['is_responsible'] = safe_eval(relation.get('is_responsible', False))
            data_relation_sanitized.append(relation)

        _logger.info('Start import relation foyer')

        if self.import_method == 'orm':
            horanet_relation_foyer = self.env['horanet.relation.foyer']
            for relation in data_relation_sanitized:
                loop_number += 1
                if loop_number % 100 == 0:
                    _logger.info('Creating relation %s' % loop_number)
                horanet_relation_foyer.create(relation)
        else:
            # import en SQL
            static_values = str(self.env.uid) + ", CURRENT_TIMESTAMP, " + str(self.env.uid) + ", CURRENT_TIMESTAMP"
            static_fields = "create_uid, create_date, write_uid, write_date"
            insert_fields = [k for (k, v) in data_relation_sanitized[0].items()]

            insert_queries = []
            for relation in data_relation_sanitized:
                values = [relation[idx] for idx in insert_fields]
                insert_queries.append(cr.mogrify("(" + static_values + ", %s" * len(values) + ')', tuple(values)))
            cr.execute(
                'INSERT INTO horanet_relation_foyer(' + static_fields + ',' + ','.join(
                    insert_fields) + ') VALUES' + ','.join(insert_queries))

        return data_relation_sanitized

    def _check_and_get_data_file(self, required_data, folder_path):
        """Check if the provided file is valid or not.

        :param required_data: dict containing file name and fields to match
        :param folder_path: string referring to the path where files are stored
        :return: dict containing path of file for a given key
        :rtype: {}
        """
        _logger.info('Scanning file content')
        list_file = dict()
        for file_name, data_label in required_data.items():
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                raise Exception('Fichier ' + file_name + ' not found')
            with open(file_path, "r") as fp:
                header_fields = fp.readline().rstrip().split(";")
            for label in data_label:
                if label not in header_fields:
                    raise Exception(
                        'Missing ' + label + ' in header of file ' + file_name + '\n' + 'file path : ' + file_path)
            list_file[file_name] = file_path
        _logger.info('File content OK')
        return list_file

    @api.multi
    def _create_external_id(self, list_tuple_name_id, model):
        """Create external id of each imported partner to be able to delete them in case of a futur import.

        :param list_tuple_name_id: list of tuple containing name and id of a partner
        :param model: model to use as value of model column in ir_model_data
        """
        cr = self.env.cr
        _logger.info('Create External ID, ' + str(len(list_tuple_name_id)) + ' records')

        static_values = str(self.env.uid) + ", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, " + str(
            self.env.uid) + ", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE, '" + str(
            self.module_name) + "', '" + model + "'"

        insert_value = ','.join(cr.mogrify("(" + static_values + ", %s, %s)", (y, x)) for x, y in list_tuple_name_id)

        cr.execute(
            'INSERT INTO ir_model_data(create_uid, create_date, write_date, write_uid, date_init, date_update,'
            ' noupdate,  module, model, name, res_id) VALUES' + insert_value)

        _logger.info('Create External ID, Done')

    def _get_data_csv(self, file_path):
        """Transform data from a CSV file to a list of dict to be able to iterate over.

        :param file_path: path of the file to extract data
        :return: list of dict that map values for column
        :rtype: [{}]
        """
        with open(file_path, "r") as f:
            data_file = [tuple(self.cast_unicode(line).rstrip().split(";")) for line in f.read().splitlines()]
        header = data_file.pop(0)
        data = []
        for partner in data_file:
            tmp = {}
            for label in header:
                idx = header.index(label)
                tmp[label] = partner[idx]
            data.append(tmp)
        return data

    @staticmethod
    def cast_unicode(string):
        if isinstance(string, str):  # nothing to do if type unicode
            try:
                string = string.decode('ascii')
            except UnicodeDecodeError:
                string = string.decode('utf-8')
        return string

    # endregion

    pass
