# -*- coding: utf-8 -*-

from odoo import models


class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    def _merge(self, partner_ids, dst_partner=None):
        u"""Descendre dans SmartIntegral la fusion des acteurs."""
        partner_dest_id = ""
        partners_source_id = ""
        fusion_smartbambi = False
        if dst_partner.tpa_membership_smartbambi:
            fusion_smartbambi = True
        data_merge = "Partner destination : " + dst_partner.lastname + " " + dst_partner.firstname + " de type " + \
                     dst_partner.company_type + ", partner(s) source(s) : "
        for partner_id in partner_ids:
            if partner_id != dst_partner.id:
                partner_source = self.env['res.partner'].search([('id', '=', partner_id)])
                # Merge dans SmartBambi
                if partner_source.tpa_membership_smartbambi:
                    tpa_exernal_id = self.env['tpa.synchronization.status'].search(
                        [('ref_partner.id', '=', partner_id), ('tpa_name', '=', 'horanet_tpa_smartbambi')])
                    partner_source.write({'tpa_membership_smartbambi': False})
                    if not fusion_smartbambi:
                        dst_partner.write({'tpa_membership_smartbambi': True})

                    tpa_exernal_id_dst = self.env['tpa.synchronization.status'].search(
                        [('ref_partner.id', '=', dst_partner.id), ('tpa_name', '=', 'horanet_tpa_smartbambi')])
                    tpa_exernal_id_dst.action_synchronization_smartbambi()
                    partner_dest_id = tpa_exernal_id_dst.external_id
                    partners_source_id = partners_source_id + str(tpa_exernal_id.external_id) + ","
                    data_merge = \
                        data_merge + partner_source.lastname \
                        + " " + partner_source.firstname \
                        + " de type " + partner_source.company_type \
                        + ", "
                    partner_source.delete_tpa_synchro_partner('horanet_tpa_smartbambi', tpa_exernal_id.external_id)

        super(MergePartnerAutomatic, self)._merge(partner_ids, dst_partner)

        # appel de la fonction de fusion si les acteurs ont une synchronisation TPA
        if partners_source_id != "":
            self._merge_tpa_smartbambi(partner_dest_id, partners_source_id, data_merge, dst_partner)

    def _merge_tpa_smartbambi(self, partner_dest_id, partners_source_id, data_merge, dst_partner):
        u"""Appeler la fonction de fusion si les acteurs ont une synchronisation TPA."""
        rec_merge = self.sudo().env['tpa.synchronization.merge'].create({
            'tpa_name': "horanet_tpa_smartbambi",
            'external_id_src': partners_source_id,
            'external_id_dest': partner_dest_id,
            'ref_partner_dest': dst_partner.id,
            'data': unicode(data_merge)})
        rec_merge.smartbambi_merge()
