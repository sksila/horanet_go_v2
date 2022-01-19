from odoo import fields, models


class ResGroups(models.Model):
    # region Private attributes
    _inherit = 'res.groups'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration

    # Surcharge du champ pour éviter de sélectionner depuis les rôles des groupes internes, cela pourrait être
    # amélioré plus tard en utilisant un domaine, plutôt qu'un filtre optionnel
    implied_ids = fields.Many2many(context="{'search_default_no_share': 1}")

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
    # endregion

    pass
