# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields

_logger = logging.getLogger(__name__)


class WebsiteApplicationStage(models.Model):
    """
    Classe permettant de regrouper les blocs d'informations en étapes.

    Une étape correspond à une page affichant n bloc(s) en front.
    Chaque page "étape" possède un bouton précédent et suivant permettant de naviguer dans les étapes.
    Un téléservice ayant plus d'une étape affiche alors un fil d'ariane horizontal, indiquant l'étape en cours.
    On ne peut passer d'une étape à la suivante que si le(s) bloc(s) qui la compose(nt) est (sont)
    correctement renseigné(s).
    """

    # region Private attributes
    _name = 'website.application.stage'
    _order = 'sequence, id'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name',
                       required=True,
                       translate=True,
                       help="The title of the stage on the online application")

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
