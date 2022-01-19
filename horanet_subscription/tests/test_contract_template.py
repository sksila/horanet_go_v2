# coding: utf-8

from functools import partial

from psycopg2 import IntegrityError

from odoo.tests import common
from odoo.exceptions import ValidationError

from .test_activity import create as create_activity
from .test_service import create as create_service
from .test_prestation import create as create_prestation
from .test_cycle import create as create_cycle


def get_default_values(env):
    # Cycles creation
    three_months_cycle = create_cycle(env, {
        'period_type': 'months',
        'period_quantity': 3
    })
    one_civil_week_cycle = create_cycle(env, {
        'period_type': 'civil_week',
        'period_quantity': 1
    })
    one_year_cycle = create_cycle(env, {
        'period_type': 'years',
        'period_quantity': 1
    })
    one_civil_year_cycle = create_cycle(env, {
        'period_type': 'civil_year',
        'period_quantity': 1
    })

    # Unit of measures creation
    m3_unit = env['product.uom'].create({
        'name': 'm3',
        'category_id': env.ref('product.product_uom_categ_vol').id,
        'uom_type': 'bigger',
        'factor_inv': 1000
    })

    # Activities creation
    wood_activity = create_activity(env, {
        'name': 'Wood',
        'product_uom_id': m3_unit.id
    })
    access_activity = create_activity(env, {'name': 'Access'})

    # Services creation
    deposit_service = create_service(env, {
        'name': 'Deposit',
        'product_uom_categ_id': env.ref('product.product_uom_categ_vol').id,
        'activity_ids': [(6, 0, [wood_activity.id])]
    })
    access_service = create_service(env, {
        'name': 'Access',
        'product_uom_categ_id': env.ref('product.product_uom_categ_unit').id,
        'activity_ids': [(6, 0, [access_activity.id])]
    })

    # Prestations creation
    individual_deposit_prestation = create_prestation(env, {
        'name': 'Deposit Individual Yearly',
        'service_id': deposit_service.id,
        'cycle_id': one_year_cycle.id
    })
    individual_access_prestation = create_prestation(env, {
        'name': 'Access Individual Yearly',
        'service_id': access_service.id,
        'cycle_id': one_year_cycle.id
    })

    professional_deposit_prestation = create_prestation(env, {
        'name': 'Deposit professional Yearly',
        'service_id': deposit_service.id,
        'cycle_id': one_year_cycle.id
    })
    professional_deposit_weekly_prestation = create_prestation(env, {
        'name': 'Deposit professional Weekly',
        'service_id': deposit_service.id,
        'cycle_id': one_civil_week_cycle.id,
        'is_blocked': True,
        'balance': 1
    })
    professional_access_prestation = create_prestation(env, {
        'name': 'Access professional Yearly',
        'service_id': access_service.id,
        'cycle_id': one_year_cycle.id
    })

    # Partner categories creation
    individual_category = env['subscription.category.partner'].create({
        'name': 'Individual',
        'domain': "[('is_company', '=', False)]",
        'code': 'INDI_CATEG'
    })
    professional_category = env['subscription.category.partner'].create({
        'name': 'Professional',
        'domain': "[('is_company', '=', True)]",
        'code': 'PRO_CATEG'
    })

    return {
        'individual': {
            'name': 'Individual',
            'prestation_ids': [(6, 0, [individual_deposit_prestation.id, individual_access_prestation.id])],
            'cycle_id': one_year_cycle.id,
            'subscription_category_ids': [(6, 0, [individual_category.id])]
        },
        'professional': {
            'name': 'Professional',
            'prestation_ids': [(6, 0, [professional_deposit_prestation.id,
                                       professional_access_prestation.id,
                                       professional_deposit_weekly_prestation.id])],
            'cycle_id': three_months_cycle.id,
            'subscription_category_ids': [(6, 0, [professional_category.id])]
        },
        'individual_renewable': {
            'name': 'Individual',
            'prestation_ids': [(6, 0, [individual_deposit_prestation.id, individual_access_prestation.id])],
            'cycle_id': one_civil_year_cycle.id,
            'subscription_category_ids': [(6, 0, [individual_category.id])]
        },
    }


def create(env, partner_category, values={}):
    default_values = get_default_values(env).get(partner_category)
    default_values.update({
        'is_renewable': True,
        'payment_type': 'after'
    })
    default_values.update(values)

    return env['horanet.subscription.template'].create(default_values)


@common.post_install(True)
class TestContractTemplate(common.TransactionCase):

    def setUp(self):
        super(TestContractTemplate, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_individual_template_pass(self):
        template = self.create('individual')

        self.assertTrue(template.exists())

    def test_02_create_professional_template_pass(self):
        template = self.create('professional')

        self.assertTrue(template.exists())

    def test_03_create_without_cycle_fail(self):
        with self.assertRaises(IntegrityError):
            self.create('individual', {'cycle_id': False})

    def test_04_create_without_prestations_fail(self):
        with self.assertRaises(ValidationError):
            self.create('individual', {'prestation_ids': False})

    def test_06_create_with_only_spaces_in_name_fail(self):
        with self.assertRaises(ValidationError):
            self.create('individual', {'name': ' '})
