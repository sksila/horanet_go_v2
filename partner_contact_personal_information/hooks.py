import logging

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    """Post-install script.

    Add gender to existing res.partner.title
    """
    _logger = logging.getLogger('odoo.addons.partner_contact_personal_information')
    _logger.info('Adding gender to existing res.partner.title')

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Update existing title gender
    with tools.ignore(Exception):
        update_existing_base_title(env)


def update_existing_base_title(env):
    """Set the gender value of existing titles."""
    title_to_update = [('base.res_partner_title_madam', 'female'),
                       ('base.res_partner_title_miss', 'female'),
                       ('base.res_partner_title_mister', 'male'),
                       ('base.res_partner_title_doctor', 'neutral'),
                       ('base.res_partner_title_prof', 'neutral')]
    for title_ext_id, gender in title_to_update:
        update_title_gender(env, title_ext_id, gender)


def update_title_gender(env, title_ext_id, gender):
    title_rec = env.ref(title_ext_id, raise_if_not_found=False)
    if title_rec:
        title_rec.gender = gender
