import logging

from odoo import models

_logger = logging.getLogger(__name__)


class EnvironmentConfig(models.Model):
    """On déclare ici le modèle de configuration utilisé par les autres modules Transport."""

    # region Private attributes
    _inherit = 'res.config.settings'
    _name = 'horanet.transport.config'
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
    # endregion

    pass
