
try:
    from odoo.addons.partner_contact_identification.tests.unit.utils import create_tag
except ImportError:
    from partner_contact_identification.tests.unit.utils import create_tag


def create_deposit_area(env, values={}):
    default_values = {
        'name': 'ZPAV 1'
    }

    default_values.update(values)

    return env['environment.deposit.area'].create(default_values)


def create_deposit_import_data(env, values={}):
    deposit_point = values.get('deposit_point', False) or create_deposit_point(env)
    tag = values.get('tag', False) or create_tag(env, "123456789")

    values.pop('deposit_point', None)
    values.pop('tag', None)

    default_values = {
        'code': 'FILE_TEST_001',
        'data': '[{"serial_number": ' + deposit_point.serial_no
                + ', "tag_number": ' + tag.number
                + ', "deposit_date": "2017-10-02 12:46:00"}]'
    }

    default_values.update(values)

    return env['deposit.import.data'].create(default_values)


def create_deposit_point(env, values={}):
    deposit_area = create_deposit_area(env)

    default_values = {
        'deposit_area_id': deposit_area.id,
        'activity_id': env.ref('environment_deposit_point.activity_papier_pav').id,
        'serial_no': '12345'
    }

    default_values.update(values)

    return env['environment.deposit.point'].create(default_values)
