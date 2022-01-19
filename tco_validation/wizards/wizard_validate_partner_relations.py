# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class ValidatePartnerRelations(models.TransientModel):
    """Allow relations validation of a partner in a convenient way displaying.

    the relations to validate and the document used to validate them.
    """

    # region Private attributes
    _name = 'horanet.citizen.wizard.validate.partner.relations'

    # endregion

    # region Default methods
    def _default_document_id(self):
        """Get the first document of the partner for a particular type.

        :return: the document to use as family record book
        """
        return self.env['ir.attachment'].search(
            [('partner_id', '=', self.env.context.get('default_partner_id')),
             ('document_type_id.technical_name', '=', 'family_record_book')],
            limit=1
        )

    # endregion

    # region Fields declaration
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner'
    )

    garant_ids = fields.Many2many(
        string='Responsable of',
        related='partner_id.garant_ids',
        readonly=True
    )

    garant_workflow = fields.Selection(
        string='Garant relation workflow state',
        related='partner_id.garant_workflow'
    )

    document_id = fields.Many2one(
        string='Document',
        comodel_name='ir.attachment',
        default=_default_document_id,
        domain="[('partner_id', '=', partner_id), \
                 ('document_type_id.technical_name', '=', 'family_record_book')]"
    )
    document_status = fields.Selection(
        string='Document status',
        related='document_id.status'
    )
    document_link = fields.Binary(
        string='Download link',
        related='document_id.datas',
        readonly=True
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_change_document_status(self, status):
        """Change the status of the document.

        :param status: the status to set to the document
        :return: the view of this wizard
        """
        self.ensure_one()

        self.document_id.change_status(status)

        context = self.env.context.copy()
        context['default_document_id'] = self.document_id.id

        return {
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res.id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_validate_relations(self):
        """Validate partner relations if the document is valid."""
        self.ensure_one()

        if self.document_id.status != 'valid':
            raise exceptions.ValidationError(
                _('The document must be valid to validate relations.')
            )

        self.partner_id.action_workflow_validate_relations()

    @api.multi
    def action_reject_relations(self):
        """Reject partner relations."""
        self.ensure_one()

        self.partner_id.action_workflow_reject_relations()
    # endregion

    # region Model methods
    # endregion
