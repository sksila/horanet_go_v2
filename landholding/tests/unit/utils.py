def create_landholding_bati(env, values={}):
    default_values = {
        'unique_id': '9999999999'
    }

    default_values.update(values)

    return env['landholding.bati'].create(default_values)


def create_landholding_prop(env, values={}):
    default_values = {
        'name': 'MR TEST TESTS'
    }

    default_values.update(values)

    return env['landholding.prop'].create(default_values)


def create_landholding_communal_account(env, values={}):
    city = values.pop('city_id', False) or env['res.city'].create({'name': 'Ville TEST'})

    default_values = {
        'name': 'Z99999',
        'city_id': city.id
    }

    default_values.update(values)

    return env['landholding.communal.account'].create(default_values)


def create_landholding_communal_account_line(env, values={}):

    default_values = {
        'real_part_right_code': 'A',
    }

    default_values.update(values)

    return env['communal.account.line'].create(default_values)
