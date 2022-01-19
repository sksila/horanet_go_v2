
import ast

from odoo import _, api, fields, exceptions, models


class PartnerCategory(models.Model):
    _inherit = 'subscription.category.partner'

    is_environment_producer = fields.Boolean(
        string="Is environment producer",
        help="Used to create menu entries for these categories",
        default=False
    )

    is_environment_staff = fields.Boolean(
        string="Is environment operator",
        help="Used to create menu entries for these categories",
        default=False
    )

    menu_id = fields.Many2one('ir.ui.menu')

    @api.onchange('application_type')
    def _on_change_application_type(self):
        if self.application_type != 'environment':
            self.is_environment_producer = False
            self.is_environment_staff = False

    @api.constrains('is_environment_producer', 'is_environment_staff', 'domain', 'name')
    def _compute_menu_id(self):
        partner_top_menu = self.env.ref('environment_waste_collect.partner_menu', False)
        operators_top_menu = self.env.ref('environment_waste_collect.waste_site_staff_menu', False)

        # In case of fresh install, the partner menu does not exists at
        # this time. We should move partner menu to horanet_environment module
        if not partner_top_menu:
            return
        if not operators_top_menu:
            return

        if self.env.context.get('domain_fixed'):
            return

        for rec in self.filtered(lambda r: r.application_type == 'environment'):
            if rec.is_environment_producer and not rec.is_environment_staff:
                rec._create_or_update_menu(partner_top_menu)
            elif rec.is_environment_staff and not rec.is_environment_producer:
                rec._create_or_update_menu(operators_top_menu)
            else:
                if rec.is_environment_producer:
                    rec.is_environment_producer = False
                if rec.is_environment_staff:
                    rec.is_environment_staff = False
                rec._delete_menu()

    @api.multi
    def _delete_menu(self):
        self.ensure_one()

        if self.menu_id:
            self._delete_translations(self.menu_id)
            self.menu_id.action.unlink()
            self.menu_id.unlink()

    @api.multi
    def _create_or_update_act_window(self):
        self.ensure_one()

        context = {
            'search_default_environment_user': True,
            'environment_partner': True
        }

        is_company = "[u'is_company', u'=', 1]"
        context['create_partner_pro'] = is_company in self.domain

        # Check for any non list element in the domain
        domain = ast.literal_eval(self.domain)
        if any(not isinstance(criteria, (list, tuple)) and criteria != '&' for criteria in domain):
            raise exceptions.UserError(_("This domain is too complex to create a menu entry"))

        context.update(self.fix_domain_and_get_context())

        if self.menu_id:
            self.menu_id.action.write({
                'name': self.name,
                'domain': self.domain,
                'context': context
            })

            return

        return self.env['ir.actions.act_window'].sudo().create({
            'name': self.name,
            'domain': self.domain,
            'context': str(context),
            'res_model': 'res.partner',
            'view_ids': [
                (0, 0, {'sequence': 1, 'view_mode': 'kanban',
                        'view_id': self.env.ref('partner_contact_citizen.citizen_kanban_view').id}),
                (0, 0, {'sequence': 2, 'view_mode': 'tree',
                        'view_id': self.env.ref('environment_waste_collect.environment_partner_view_tree').id}),
                (0, 0, {'sequence': 3, 'view_mode': 'form',
                        'view_id': self.env.ref('environment_waste_collect.res_partner_form_view').id})
            ],
            'search_view_id': self.env.ref('environment_waste_collect.view_res_partner_filter').id,
            'groups_id': [(4, self.env.ref('horanet_environment.group_browse_environment').id)]
        })

    @api.multi
    def _create_or_update_menu(self, parent_menu, values={}):
        self.ensure_one()

        if self.menu_id:
            if self.name != self.menu_id.name:
                self.menu_id.name = self.name
            self._create_or_update_act_window()
        else:
            action = self._create_or_update_act_window()

            self.menu_id = self.env['ir.ui.menu'].sudo().create({
                'name': self.name,
                'parent_id': parent_menu.id,
                'action': 'ir.actions.act_window,%s' % action.id,
                'groups_id': [(4, self.env.ref('horanet_environment.group_browse_environment').id)]
            })

        self._create_or_update_translations(self.menu_id)

    @api.multi
    def _create_or_update_translations(self, menu):
        self.ensure_one()

        translation_model = self.env['ir.translation'].sudo()

        self._delete_translations(menu)

        record_translation = translation_model.search([
            ('name', '=', self._name + ',name'),
            ('res_id', '=', self.id)
        ])

        if record_translation:
            menu_translation = record_translation.copy()
            action_translation = record_translation.copy()

            menu_translation.write({'name': 'ir.ui.menu,name', 'res_id': menu.id})
            action_translation.write({'name': 'ir.actions.act_window,name', 'res_id': menu.action.id})
        else:
            translation_model.create({'name': 'ir.ui.menu,name', 'res_id': menu.id})
            translation_model.create({'name': 'ir.actions.act_window,name', 'res_id': menu.action.id})

    @api.model
    def _delete_translations(self, menu):
        translation_model = self.env['ir.translation'].sudo()
        translation_model.search([
            ('name', '=', 'ir.ui.menu,name'),
            ('res_id', '=', menu.id)
        ]).unlink()
        translation_model.search([
            ('name', '=', 'ir.actions.act_window,name'),
            ('res_id', '=', menu.action.id)
        ]).unlink()
