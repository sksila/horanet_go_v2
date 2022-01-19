# coding: utf-8

import json

from odoo import api, SUPERUSER_ID


def create_waste_site_model(model, values):
    """Create a record of model `waste_site`.

    :param model: model used to create record
    :param values: values used to create record
    """
    model.env.cr.execute(
        'DELETE FROM procurement_rule WHERE picking_type_id '
        'IN (SELECT id FROM stock_picking_type WHERE warehouse_id = %s)'
        % values.get('id')
    )

    model.env.cr.execute(
        'DELETE FROM stock_warehouse WHERE id = (%s)'
        % values.get('id')
    )
    return model.create({
        'name': values.get('name'),
        'smarteco_waste_site_id': values.get('smarteco_warehouse_id'),
        'partner_id': values.get('partner_id'),
        'email': 'no@mail.com',  # une valeur NULL viole la contrainte NOT NULL de la colonne « email »
    })


def insert_activities(cr):
    """Link activity instead of product.

    Load generated data file to link all activities needed by others models
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        json_data = open('/tmp/data-product-before-10.0.17.6.6.json')
        data = json.load(json_data)

        activity_model = env['horanet.activity']
        emplacement_model = env['stock.emplacement']
        contract_model = env['environment.pickup.contract']

        for k, v in data['emplacements'].items():
            if not v:
                continue

            activity = activity_model.search([('name', '=', v.get('name'))])

            emplacement = emplacement_model.browse(int(k))
            emplacement.activity_id = activity.id

        for k, v in data['contracts'].items():
            if not v:
                continue

            activities = activity_model.search([('name', 'in', v)])

            contract = contract_model.browse(int(k))
            contract.activity_ids = [(6, 0, activities.ids)]


def insert_waste_sites(cr):
    """Insert waste sites into database.

    Load generated data file to insert all waste sites
    needed by others models
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        json_data = open('/tmp/data-warehouse-before-10.0.17.6.6.json')
        data = json.load(json_data)

        waste_site_model = env['environment.waste.site']
        container_model = env['environment.container']
        emplacement_model = env['stock.emplacement']
        contract_model = env['environment.pickup.contract']

        for k, v in data['containers'].items():
            waste_site = waste_site_model.search([('name', '=', v.get('name'))])
            if not waste_site:
                waste_site = create_waste_site_model(waste_site_model, v)
            container = container_model.browse(int(k))
            container.waste_site_id = waste_site.id

        for k, v in data['emplacements'].items():
            waste_site = waste_site_model.search([('name', '=', v.get('name'))])
            if not waste_site:
                waste_site = create_waste_site_model(waste_site_model, v)
            emplacement = emplacement_model.browse(int(k))
            emplacement.waste_site_id = waste_site.id

        for k, v in data['contracts'].items():
            waste_site = waste_site_model.search([('name', '=', v.get('name'))])
            if not waste_site:
                waste_site = create_waste_site_model(waste_site_model, v)
            contract = contract_model.browse(int(k))
            contract.waste_site_id = waste_site.id


def migrate(cr, version):
    if not version:
        return

    insert_waste_sites(cr)
    insert_activities(cr)
