import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PortalWizard(models.TransientModel):
    """Surcharge du modèle portal wizard pour y ajouter la possibilité de sélectionner/déselectionner tout."""

    # region Private attributes
    _inherit = 'portal.wizard'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    toggle_portal = fields.Boolean(
        string="Toogle all \"in portal\"",
        default=False,
        help="Toggle all partner, to remove or grant a portal access the the entire list")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('toggle_portal')
    def onchange_toggle_portal(self):
        """Permet de modifier les valeurs du wizard sans devoir le recharger (contrairement aux actions)."""
        if self.toggle_portal:
            for rec in self.user_ids:
                rec.in_portal = True
        else:
            for rec in self.user_ids:
                rec.in_portal = False

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
