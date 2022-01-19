from datetime import date, datetime

from odoo import api, models, fields


class Tag(models.Model):
    """Add method to facilitate subscription operations.

    A tag is a unique identifier used to authenticate a citizen against collectivity services
    """

    # region Private attributes
    _inherit = 'partner.contact.identification.tag'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_tag_linked_package(self, given_date=None):
        """Return all packages linked to a Tag (via it's assignation).

        :param given_date: a date to filter on assignations
        :return: recorset of horanet.package linked to the tag
        """
        self.ensure_one()
        packages = self.env['horanet.package']
        assignation_model = self.env['partner.contact.identification.assignation']

        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        given_date = given_date or self.env.context.get('force_time', datetime.now())
        if isinstance(given_date, (datetime, date)):
            given_date = fields.Datetime.to_string(given_date)
        elif isinstance(given_date, str):
            given_date = fields.Datetime.to_string(fields.Datetime.from_string(given_date))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        active_assignation_domain = assignation_model.search_is_active(operator='=', value=True, search_date=given_date)
        assignations = assignation_model.search(
            ['&', ('reference_id', '!=', False), ('tag_id', '=', self.id)] + active_assignation_domain)

        for assignation in assignations:
            if assignation.reference_id._name == 'horanet.package':
                packages += assignation.reference_id
            elif assignation.partner_id:
                packages += packages.search([('recipient_id', '=', assignation.partner_id.id)])

        # Trick to remove duplicates
        packages = packages & packages

        return packages & packages

    # endregion

    pass
