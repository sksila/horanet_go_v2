# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields

_logger = logging.getLogger(__name__)


class WebsiteApplicationBlock(models.Model):
    """
    Classe permettant de regrouper des informations complémentaires du modèle.

    Un bloc correspond à un ensemble de champs de saisie (texte, document etc.) et possède un libellé.
    Les blocs composant un modèle de demande en ligne sont ordonnés.
    Les informations d'un bloc peuvent être affichées sur plusieurs colonnes.
    """

    # region Private attributes
    _name = 'website.application.block'
    _order = 'sequence, id'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help="The title of the block on the online application"
    )

    sequence = fields.Integer(string="Sequence")
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
