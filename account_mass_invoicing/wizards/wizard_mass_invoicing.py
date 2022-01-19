# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports from odoo
from odoo import models, api, fields, _

logger = logging.getLogger(__name__)


class ResetAndImportDataFr(models.TransientModel):
    """Class of import methods."""

    # region Private attributes
    _name = 'wizard.mass.invoicing'

    # endregion

    # region Default methods
    @api.model
    def _get_default_batch_types(self):
        return self.env['horanet.invoice.batch.type'].search([])

    # endregion

    # region Fields declaration
    batch_type_ids = fields.Many2many(
        string="Batch types",
        comodel_name='horanet.invoice.batch.type',
        default=_get_default_batch_types,
    )
    campaign_id = fields.Many2one(
        string="Campaign",
        comodel_name='horanet.invoice.campaign',
        required=True,
    )
    result = fields.Html(
        string="Result",
        readonly=True,
    )

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_mass_invoicing(self):
        result = ''
        #  Pour chaque type de lot
        for batch_type in self.batch_type_ids:
            result += '<b>' + _("Mass invoicing for bacth type %s") % batch_type.name + '</b>\n'

            # Création du lot
            batch = self.env['horanet.invoice.batch'].create({
                'type_id': batch_type.id,
                'campaign_id': self.campaign_id.id,
            })

            #  Génération des factures
            result += batch.action_generate()

        self.result = result.replace(u'\n', u'<br>').replace(u'\t', u'&emsp;')

        return self._refresh_wizard()

    # endregion

    # region Model methods
    @api.multi
    def _refresh_wizard(self):
        self.ensure_one()

        # Rappel du wizard en gardant son contexte
        return {
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # endregion

    pass
