try:
    from odoo.addons.website.controllers.main import Website
except ImportError:
    from website.controllers.main import Website

from odoo import http
from odoo.http import request


class InheritWebsite(Website):

    @http.route()
    def get_website_translations(self, lang, mods=None):
        u"""Surcharge afin d'ajouter les modules dépendant d'horanet_website à la liste des traductions en front."""
        depend_model = request.env['ir.module.module.dependency'].sudo()
        module_ids = [dep['module_id'][0] for dep in depend_model.search_read(
            [('name', '=', 'horanet_website')], ['module_id'])]

        horanet_website_module = [module['name'] for module in request.env['ir.module.module'].sudo().search_read([
            ('id', 'in', module_ids),
            ('name', 'not ilike', 'website'),
            ('state', '=', 'installed')],
            ['name'])]

        mods.extend(horanet_website_module)

        return super(InheritWebsite, self).get_website_translations(lang, mods)
