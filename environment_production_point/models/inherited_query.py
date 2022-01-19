# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.osv import expression


class PartnerMoveInheritedQuery(models.Model):
    """Surcharge du moteur de calcul."""

    # region Private attributes
    _inherit = 'device.query'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    def _search_query_partner_id(self, operator, value):
        u"""Override of the search method of query_partner_id.

        Add search method to find operation partner if the tag is assigned to a move

        :param operator: the search operator
        :param value: string for a search by name, or int or list(<int>) for a search by id
        :return: A search domain
        """
        inherited_domain = super(PartnerMoveInheritedQuery, self)._search_query_partner_id(operator, value)

        if isinstance(value, basestring):
            value = self.env['res.partner'].with_context(prefetch_fields=False).search([('name', 'ilike', value)]).ids
            value = list(value)
        if isinstance(value, int):
            value = [value]

        domain = []
        partner_move = self.env['partner.move'].search([('partner_id', 'in', value)])

        partner_assignation = self.env['partner.contact.identification.assignation'].search(
            [('move_id', 'in', partner_move.ids)])

        for assignation in partner_assignation:
            # on explicite tag_id != False car tag_id est un many2one non obligatoire, donc il peut avoir une valeur
            # null. Or si on ne l'explicite pas, lors d'une recherche négative odoo ne prendra pas en compte ceux ayant,
            # une valeur null.
            assignation_domain = [('tag_id', '!=', False),
                                  ('tag_id', '=', assignation.tag_id.id),
                                  ('time', '>=', assignation.start_date)]

            if assignation.end_date:
                assignation_domain += [('time', '<', assignation.end_date)]
            domain = expression.OR([domain, expression.normalize_domain(assignation_domain)])
        domain = expression.normalize_domain(domain)

        if operator in expression.NEGATIVE_TERM_OPERATORS and domain != []:
            domain = [expression.NOT_OPERATOR] + domain
            final_domain = expression.AND([domain, inherited_domain])
        else:
            final_domain = expression.OR([domain, inherited_domain])

        return expression.normalize_domain(final_domain)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def get_query_linked_packages(self, force_time=False):
        u"""Permet de retrouver les forfaits correspondant au paramétrage d'une query."""
        self.ensure_one()
        search_time = force_time or self.time or self.env.context.get('force_time', fields.Datetime.now())

        if self.tag_id:
            assignation_model = self.env['partner.contact.identification.assignation']
            search_active_domain = assignation_model.search_is_active('=', 'active', search_date=search_time)
            assignations = assignation_model.search(
                ['&', ('reference_id', '!=', False), ('tag_id', '=', self.tag_id.id)] + search_active_domain)
            if assignations and assignations[0].move_id:
                # Si le tag représente un emménagement, retourner les contrats liées au partner de l'eménagement
                packages = self.env['horanet.package']
                log = ''
                move_rec = assignations[0].move_id
                if move_rec.partner_id:
                    packages = packages.search([('recipient_id', '=', move_rec.partner_id.id)])
                    log += u"\n\tResolve packages using Tag -> Move({move_id}) -> Partner {partner_hyperlink}".format(
                        move_id=str(move_rec.id),
                        partner_hyperlink=(u'<a href=\"/web#id={model_id}&view_type=form&model=res.partner\">'
                                           u'{text}</a>').format(
                            model_id=unicode(move_rec.partner_id.id),
                            text=move_rec.partner_id.name + ' - ' + str(move_rec.partner_id.id)))
                    return packages, log
                else:
                    log = u"\n\tThe Tag is assigned to a move (id:{move_id}), but no partner found on the move".format(
                        move_id=str(move_rec.id))
                    return packages, log

        return super(PartnerMoveInheritedQuery, self).get_query_linked_packages(force_time=force_time)

    # endregion

    pass
