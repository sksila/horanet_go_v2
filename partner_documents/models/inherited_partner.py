from odoo import api, models


class Partner(models.Model):
    """Extend res.partner to be able to search attached documents."""

    # region Private attributes
    _inherit = 'res.partner'

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
    def get_attached_documents(self, document_id=None, document_type=None, status=None):
        """Search and return document for a res.partner.

        :param document_id: id of the ir.attachment to filter on
        :param document_type: technical_name of ir.attachment.type to filter on
        :param status: list of status to filter on
        """
        self.ensure_one()

        attachment_model = self.env['ir.attachment']
        domain = [('partner_id', '=', self.id)]

        if document_id:
            domain.append(('id', '=', document_id))
        if document_type:
            domain.append(('document_type_id.technical_name', '=', document_type))
        if status:
            domain.append(('status', 'in', status))

        return attachment_model.search(domain)

    # endregion

    pass
