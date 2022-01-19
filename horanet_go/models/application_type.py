import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ApplicationType(models.AbstractModel):
    """This model represent an application type, exemple : environment."""

    # region Private attributes
    _name = 'application.type'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    application_type = fields.Selection(String="Application type", selection=[], default=False)

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
