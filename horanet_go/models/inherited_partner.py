import ast

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    """Add 'subscription.category.partner' on partners."""

    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    subscription_category_ids = fields.Many2many(
        string="Subscription categories",
        comodel_name='subscription.category.partner',
        compute='_compute_subscription_category_ids',
        search='_search_subscription_category_ids',
        readonly=True,
        store=False,
    )

    # endregion

    # region Fields method
    @api.depends()
    def _compute_subscription_category_ids(self):
        """Détermine l'ensemble des catégories auquelles ce partner appartient."""
        partner_cate_model = self.env['subscription.category.partner']
        categories = partner_cate_model.search([])
        id_by_cate = {}

        # Recherche des partners par catégories, afin de ne pas interroger en boucle la BDD
        for cate in categories:
            cate_domain = ast.literal_eval(cate.domain)
            # limiter la recherche aux id des partners permet de gagner en performance (id = index)
            cate_domain = expression.normalize_domain(expression.AND([[('id', 'in', self.ids)], cate_domain]))
            id_by_cate.update({cate: self.search(cate_domain).ids})

        # Pour chaque partner, rechercher si il appartient à une catégorie précédemment résolue
        for rec in self:
            partner_categories = self.env['subscription.category.partner']
            for cate in categories:
                if rec.id in id_by_cate[cate]:
                    partner_categories += cate
            rec.subscription_category_ids = partner_categories

    @api.model
    def _search_subscription_category_ids(self, operator, value):
        """Recherche de partner ayant une ou plusieurs catégories.

        :param operator: Un des opérateurs suivant : 'in', 'not in', '=', '!=', 'like', 'ilike'
        :param value: une catégorie (record), un id ou une liste d'id de catégorie, ou le code de la catégorie
        :return: Un domaine de recherche de res.partner
        """
        result = expression.FALSE_DOMAIN

        if isinstance(value, str):
            categories = self.subscription_category_ids.search([('code', operator, value)])
        elif operator in ['in', 'not in', '=', '!=']:
            categories = self.env['subscription.category.partner']
            if isinstance(value, models.Model) and value._name == 'subscription.category.partner':
                categories = value
            elif value and not isinstance(value, list) and isinstance(value, int):
                categories = categories.browse([value])
            elif value and isinstance(value, list):
                categories = categories.browse(value)

        domains = [expression.normalize_domain(ast.literal_eval(domain)) for domain in categories.mapped('domain')]
        if domains:
            result = expression.AND(domains)
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            result = [expression.NOT_OPERATOR] + result

        return expression.normalize_domain(result)

    # endregion

    # region Constrains and Onchange

    @api.constrains('ref')
    def _check_unicity_partner_ref(self):
        """Check if the field ref on partner is unique when the config parameter value is true."""
        ir_property_obj = self.env['ir.config_parameter']
        use_unicity = ir_property_obj.get_param(
            'horanet_go.unicity_on_partner_internal_ref', False)

        if use_unicity:
            domain = [('ref', '=', self.ref), ('id', '!=', self.id)]
            ref_count = self.search_count(domain)
            if ref_count > 0:
                raise ValidationError(
                    _("A partner with this internal reference: '{ref}' already exits.").format(
                        ref=self.ref,
                    ))

    # endregion

    # region CRUD (overrides)

    @api.model
    def create(self, vals):
        """Create a partner with a internal reference by sequence when the config parameter is True."""
        ir_property_obj = self.env['ir.config_parameter']
        use_sequence = ir_property_obj.get_param(
            'horanet_go.use_sequence_partner_internal_ref', False)

        sequence = self.env['ir.sequence'].sudo().search([('code', '=', 'horanet.partner.internal.reference')])
        if 'ref' in vals:
            if (use_sequence and not vals['ref']) or \
                    (vals['ref'] == str(sequence.number_next_actual).zfill(sequence.padding)):
                vals['ref'] = self.env['ir.sequence'].sudo().next_by_code('horanet.partner.internal.reference')

        elif use_sequence:
            vals['ref'] = self.env['ir.sequence'].sudo().next_by_code('horanet.partner.internal.reference')

        return super(ResPartner, self).create(vals)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
