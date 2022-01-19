# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductPublicCategory(models.Model):
    """Override ProductPublicCategory class.

    Add published mixin to know if category is published on website or not.
    """

    # region Private attributes
    _name = 'product.public.category'
    _inherit = ['product.public.category', 'website.published.mixin']

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    website_published = fields.Boolean(
        default=True,
        help="View or not the category in the category list of the website store."
    )

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
