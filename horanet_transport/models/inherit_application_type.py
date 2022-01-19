import logging

from odoo import models, fields
from ..config import config

_logger = logging.getLogger(__name__)


class EnvironmentApplicationType(models.AbstractModel):
    """This model represent an application type, exemple : environment."""

    # region Private attributes
    _inherit = 'application.type'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    application_type = fields.Selection(selection_add=[(config.TYPE_TRANSPORT, "Transport")])

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
