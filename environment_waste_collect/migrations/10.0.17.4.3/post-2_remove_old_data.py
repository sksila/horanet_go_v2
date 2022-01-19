# coding: utf-8


def migrate(cr, version):
    """Remove old data uneeded anymore.

    Data removed:
        - product.attribute
        - product.attribute.value
        - product.attribute.line
        - product.template (old ones)
        - product.product (deleted from templates)
    """
    if not version:
        return

    cr.execute("DELETE FROM product_attribute_line;")
    cr.execute("DELETE FROM product_attribute_value;")
    cr.execute("DELETE FROM product_attribute;")
    cr.execute("DELETE FROM product_template WHERE name = 'Safe waste';")
    cr.execute("DELETE FROM product_template WHERE name = 'Dangerous waste';")
