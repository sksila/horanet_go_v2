from odoo import api, models


class User(models.Model):
    """Extend res.users to be able to manage attached documents."""

    # region Private attributes
    _inherit = 'res.users'

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
    def get_documents(self, document_id=None, document_type=None, status=None, date_begin=None, date_end=None):
        """Search and return document for a res.users.

        :param document_id: id of the ir.attachment to filter on
        :param document_type: technical_name of ir.attachment.type to filter on
        :param status: list of status to filter on
        """
        self.ensure_one()

        attachment_model = self.env['ir.attachment']
        domain = [('user_id', '=', self.id)]

        if document_id:
            domain.append(('id', '=', document_id))
        if document_type:
            domain.append(('document_type_id.technical_name', '=', document_type))
        if status:
            domain.append(('status', 'in', status))
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<', date_end)]

        return attachment_model.search(domain)

    @api.multi
    def delete_document(self, document_id):
        """Delete an ir.attachment that belongs the current user.

        :param document_id: id of the or.attachment to delete
        """
        self.ensure_one()
        attachment_model = self.env['ir.attachment']

        attachment_model.search([
            ('id', '=', document_id),
            ('user_id', '=', self.id)
        ]).unlink()

    # endregion

    pass
