# -*- coding: utf-8 -*-

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    u"""
    Post-install script.

    Migration des pays pour ajouter le prefix d'appel national et le prefix mobile.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    migrate_countries(env)


def migrate_countries(env):
    """Method to attribute national prefix and mobile prefix."""
    _logger.info("Starting Migration of countries")

    countries = env['res.country'].search([])
    # Data National prefix
    countries.filtered(
        lambda r: r.code in ['AE', 'AF', 'AL', 'AM', 'AN', 'AO', 'AR', 'AT', 'AU', 'AZ', 'BA', 'BD', 'BE', 'BG',
                             'BO', 'BR', 'CD', 'CH', 'CN', 'CO', 'CU', 'DE', 'DZ', 'EC', 'EG', 'ER', 'ET', 'FI',
                             'FR', 'GE', 'GH', 'GR', 'HR', 'ID', 'IE', 'IL', 'IN', 'IQ', 'IR', 'JO', 'JP', 'KE',
                             'KG', 'KH', 'KP', 'KR', 'LA', 'LB', 'LK', 'LT', 'LY', 'MA', 'MD', 'ME', 'MK', 'MM',
                             'MN', 'MY', 'NA', 'NG', 'NL', 'NP', 'NZ', 'PE', 'PH', 'PK', 'PL', 'PY', 'RO', 'RS',
                             'SA', 'SD', 'SE', 'SG', 'SI', 'SH', 'SL', 'SR', 'SS', 'SY', 'TH', 'TR', 'TW', 'TZ',
                             'UA', 'UG', 'GB', 'UY', 'VE', 'VN', 'YE', 'ZA', 'ZM', 'ZW']).write(
        {'national_prefix': "0"})

    countries.filtered(lambda r: r.code in ['CA', 'FM', 'MH', 'US']).write({'national_prefix': "1"})
    countries.filtered(lambda r: r.code in ['BY', 'KZ', 'RU', 'TJ', 'TM', 'UZ']).write({'national_prefix': "8"})
    countries.filtered(lambda r: r.code in ['MX']).write({'national_prefix': "01"})
    countries.filtered(lambda r: r.code in ['HU']).write({'national_prefix': "06"})

    # Data Mobile prefix
    countries_prefix_9 = countries.filtered(
        lambda r: r.code in ['DZ', 'AO', 'AR', 'CL', 'CY', 'HR', 'DK', 'EC', 'HK', 'IN',
                             'NO', 'PE', 'PT', 'RU', 'SG', 'SK', 'TW', 'TN'])
    countries_prefix_8 = countries.filtered(
        lambda r: r.code in ['BG', 'CR', 'DK', 'EE', 'IN', 'IE', 'IS', 'PL', 'SG', 'TH'])
    countries_prefix_7 = countries.filtered(
        lambda r: r.code in ['AF', 'DZ', 'BO', 'CR', 'DK', 'ES', 'FR', 'HU', 'IN', 'IS',
                             'KZ', 'MK', 'PL', 'RO', 'UK', 'SI', 'SE', 'CH'])
    countries_prefix_6 = countries.filtered(
        lambda r: r.code in ['AL', 'DZ', 'AD', 'AT', 'BO', 'BA', 'DK', 'ES', 'FR', 'GR',
                             'GP', 'HK', 'IS', 'LT', 'LU', 'MA', 'NL', 'PL', 'RS', 'SI'])
    countries_prefix_5 = countries.filtered(
        lambda r: r.code in ['DZ', 'SA', 'DK', 'AE', 'EE', 'FI', 'HK', 'IL', 'PL', 'SI', 'TN', 'TK'])
    countries_prefix_4 = countries.filtered(lambda r: r.code in ['AD', 'AU', 'BE', 'DK', 'FI', 'MC', 'NO', 'RS', 'SI',
                                                                 'TN', 'VE'])
    countries_prefix_3 = countries.filtered(lambda r: r.code in ['AD', 'CO', 'DK', 'HU', 'IT', 'MG', 'SI', 'VA'])
    countries_prefix_2 = countries.filtered(lambda r: r.code in ['DK', 'HU', 'LV', 'NZ', 'TN'])
    countries_prefix_1 = countries.filtered(lambda r: r.code in ['DE', 'AU', 'CN', 'KR', 'EG', 'MY', 'MX'])

    for country in countries:
        country.mobile_prefix = ""
        if country in countries_prefix_9:
            country.write({'mobile_prefix': country.mobile_prefix + "9,"})
        if country in countries_prefix_8:
            country.write({'mobile_prefix': country.mobile_prefix + "8,"})
        if country in countries_prefix_7:
            country.write({'mobile_prefix': country.mobile_prefix + "7,"})
        if country in countries_prefix_6:
            country.write({'mobile_prefix': country.mobile_prefix + "6,"})
        if country in countries_prefix_5:
            country.write({'mobile_prefix': country.mobile_prefix + "5,"})
        if country in countries_prefix_4:
            country.write({'mobile_prefix': country.mobile_prefix + "4,"})
        if country in countries_prefix_3:
            country.write({'mobile_prefix': country.mobile_prefix + "3,"})
        if country in countries_prefix_2:
            country.write({'mobile_prefix': country.mobile_prefix + "2,"})
        if country in countries_prefix_1:
            country.write({'mobile_prefix': country.mobile_prefix + "1,"})
        country.mobile_prefix = country.mobile_prefix[:-1]
