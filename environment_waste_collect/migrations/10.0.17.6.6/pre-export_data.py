# coding: utf-8

import json


def export_warehouse_relations(cr):
    """Export relations between our models and stock.warehouse.

    Take containers, emplacements and contracts with warehouse_id
    to be able to insert them again as environment.waste.site
    """
    cr.execute('SELECT id, name, smarteco_warehouse_id, partner_id '
               'FROM stock_warehouse;')
    warehouses_tmp = cr.fetchall()
    warehouses = {w[0]: {'id': w[0], 'name': w[1], 'smarteco_warehouse_id': w[2], 'partner_id': w[3]}
                  for w in warehouses_tmp}

    cr.execute('SELECT id, warehouse_id FROM environment_container;')
    containers_tmp = cr.fetchall()
    containers = {c[0]: c[1] for c in containers_tmp}
    for k, v in containers.items():
        containers[k] = warehouses.get(v)

    cr.execute('SELECT id, warehouse_id FROM stock_emplacement;')
    emplacements_tmp = cr.fetchall()
    emplacements = {e[0]: e[1] for e in emplacements_tmp}
    for k, v in emplacements.items():
        emplacements[k] = warehouses.get(v)

    cr.execute('SELECT id, warehouse_id FROM environment_pickup_contract;')
    contracts_tmp = cr.fetchall()
    contracts = {c[0]: c[1] for c in contracts_tmp}
    for k, v in contracts.items():
        contracts[k] = warehouses.get(v)

    data = {}
    data['containers'] = containers
    data['emplacements'] = emplacements
    data['contracts'] = contracts

    json_data = json.dumps(data)

    with open('/tmp/data-warehouse-before-10.0.17.6.6.json', 'w') as file:
        file.write(json_data)


def export_product_relations(cr):
    """Export relations between our models and product.product.

    Take emplacements and contracts with product_id
    to be able to insert them again as environment.waste.site
    """
    cr.execute('SELECT product_product.id, product_template.name FROM product_product '
               'INNER JOIN product_template ON product_product.product_tmpl_id = product_template.id '
               'ORDER BY product_product.id')
    products_tmp = cr.fetchall()
    products = {p[0]: {'id': p[0], 'name': p[1]} for p in products_tmp}

    cr.execute('SELECT id, waste_id FROM stock_emplacement;')
    emplacements_tmp = cr.fetchall()
    emplacements = {e[0]: e[1] for e in emplacements_tmp}
    for k, v in emplacements.items():
        emplacements[k] = products.get(v)

    cr.execute('SELECT id FROM environment_pickup_contract;')
    contracts_tmp = cr.fetchall()
    contracts = {c[0]: None for c in contracts_tmp}

    for k, v in contracts.items():
        cr.execute('SELECT product_product_id '
                   'FROM environment_pickup_contract_product_product_rel '
                   'WHERE environment_pickup_contract_id = %s' % k)
        relations_tmp = cr.fetchall()

        contracts[k] = [products.get(r[0]).get('name') for r in relations_tmp]

    data = {}
    data['emplacements'] = emplacements
    data['contracts'] = contracts

    json_data = json.dumps(data)

    with open('/tmp/data-product-before-10.0.17.6.6.json', 'w') as file:
        file.write(json_data)


def migrate(cr, version):
    if not version:
        return

    export_warehouse_relations(cr)
    export_product_relations(cr)
