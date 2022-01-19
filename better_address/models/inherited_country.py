from odoo import models, fields


class ResCountry(models.Model):
    """Surcharge du modèle partner pour y ajouter le modèle d'adresse."""

    # region Private attributes
    _inherit = 'res.country'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    address_format = fields.Text(help="""You can state here the usual format to use for the addresses belonging \
    to this country.\n\nYou can use the python-style string pattern with all the field of the address \
    (for example, use '%(street)s' to display the field 'street') plus
                \n%(state_name)s: the name of the state
                \n%(state_code)s: the code of the state
                \n%(country_name)s: the name of the country
                \n%(country_code)s: the code of the country""", )

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
