# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class ValidatePartnerAddress(models.TransientModel):
    """Allow address validation of a partner in a convenient way displaying.

    the address to validate and the document used to validate it.
    """

    # region Private attributes
    _name = 'horanet.citizen.wizard.validate.partner.address'

    # endregion

    # region Default methods
    def _default_document_id(self):
        """Get the first document of the partner for a particular type.

        :return: the document to use as proof of address
        """
        return self.env['ir.attachment'].search(
            [('partner_id', '=', self.env.context.get('default_partner_id')),
             ('document_type_id.technical_name', '=', 'proof_of_address')],
            limit=1
        )

    # endregion

    # region Fields declaration
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner'
    )

    street = fields.Char(
        string='Street',
        related='partner_id.street_id.name'
    )
    city = fields.Char(
        string='City',
        related='partner_id.city_id.name'
    )
    state_id = fields.Many2one(
        string='State',
        related='partner_id.state_id',
        readonly=True
    )
    country_id = fields.Many2one(
        string='Country',
        related='partner_id.country_id',
        readonly=True
    )
    street_number_id = fields.Many2one(
        string='Street number',
        related='partner_id.street_number_id',
        readonly=True
    )
    address_status = fields.Selection(
        string='Address State',
        related='partner_id.address_status'
    )
    address_workflow = fields.Selection(
        string='Address workflow state',
        related='partner_id.address_workflow'
    )

    document_id = fields.Many2one(
        string='Document',
        comodel_name='ir.attachment',
        default=_default_document_id,
        domain="[('partner_id', '=', partner_id), \
                 ('document_type_id.technical_name', '=', 'proof_of_address')]"
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
    def action_validate_address(self):
        """Validate partner address if the document is valid."""
        self.ensure_one()

        if self.document_id.status != 'valid':
            raise exceptions.ValidationError(
                _('The document must be valid to validate address.')
            )

        self.partner_id.action_workflow_validate_address()

    @api.multi
    def action_reject_address(self):
        """Reject partner address."""
        self.ensure_one()

        self.partner_id.action_workflow_reject_address()
    # endregion

    # region Model methods
    # endregion
