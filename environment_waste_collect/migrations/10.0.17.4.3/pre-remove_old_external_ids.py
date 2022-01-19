# coding: utf8


def migrate(cr, version):
    """Remove external ids of old product variants.

    Prior to this version, two products were created with some variants
    in it.

    Now that we define each product, we have to remove previous
    external ids to allow import of the new ones.
    """
    if not version:
        return

    cr.execute("DELETE FROM ir_model_data WHERE model = 'product.attribute';")
    cr.execute("DELETE FROM ir_model_data WHERE model = 'product.attribute.value';")
    cr.execute("DELETE FROM ir_model_data WHERE model = 'product.attribute.line';")
    cr.execute("DELETE FROM ir_model_data WHERE model = 'product.template';")
    cr.execute("DELETE FROM ir_model_data WHERE model = 'product.product';")
