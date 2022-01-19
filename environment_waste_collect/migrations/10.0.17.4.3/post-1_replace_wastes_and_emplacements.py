# coding: utf8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Replace old product variants with new ones created.

    As we created new products, new variants are created and old
    ones needs to be replaced by ones in emplacements.
    """
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        emplacement_model = env['stock.emplacement']
        product_model = env['product.template']
        emplacements = emplacement_model.search([])

        for emplacement in emplacements:
            product = emplacement.waste_id
            product_template = product_model.search(
                [('name', '=', product.attribute_value_ids.name)]
            )

            if product.attribute_value_ids.name == 'Metaux':
                product_template = product_model.search(
                    [('name', '=', 'Métaux')]
                )
            elif product.attribute_value_ids.name == 'Amiente-Ciment':
                product_template = product_model.search(
                    [('name', '=', 'Amiante-Ciment')]
                )
            elif product.attribute_value_ids.name == u'Activité Soin':
                product_template = product_model.search(
                    [('name', '=', 'Activité de soin')]
                )
            elif product.attribute_value_ids.name == 'Huile friture':
                product_template = product_model.search(
                    [('name', '=', 'Huile de friture')]
                )
            elif product.attribute_value_ids.name == 'Liquide de frein':
                product_template = product_model.search(
                    [('name', '=', 'Liquide de freins')]
                )
            elif product.attribute_value_ids.name == u'Petit appareil ménagers':
                product_template = product_model.search(
                    [('name', '=', 'Petit appareil ménager')]
                )
            elif product.attribute_value_ids.name == 'Piles-Boutons':
                product_template = product_model.search(
                    [('name', '=', 'Piles boutons')]
                )
            elif product.attribute_value_ids.name == u'Réfrigérateurs-Congélateurs':
                product_template = product_model.search(
                    [('name', '=', 'Réfrigérateur-Congélateur')]
                )

            emplacement.waste_id = product_template.product_variant_id.id
