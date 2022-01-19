# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields

_logger = logging.getLogger(__name__)


class WebsiteApplicationFunctionality(models.Model):
    """
    Classe permettant de joindre des informations complémentaire au modèle d'application.

    Le but est de pouvoir rajouter des informations de type basique (nombre, chaîne, ...) au modèle d'application
    pouvant servir à la validation de l'application par l'utilisateur back office.
    Ces informations seront enregistrées dans le champ texte de l'application.
    """

    # region Private attributes
    _name = 'application.functionality'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name',
                       required=True,
                       translate=True,
                       help="The text of the application's functionality")
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
