# -*- coding: utf-8 -*-
import datetime

from odoo import models


class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    def _merge(self, partner_ids, dst_partner=None):
        u"""Descendre dans SmartIntegral la fusion des acteurs."""
        partner_dest_id = ""
        partners_source_id = ""
        fusion_smarteco = False
        if dst_partner.tpa_membership_smarteco:
            fusion_smarteco = True
        data_merge = "Partner destination : " + dst_partner.lastname + " " + dst_partner.firstname + " de type " + \
                     dst_partner.company_type + ", partner(s) source(s) : "
        for partner_id in partner_ids:
            if partner_id != dst_partner.id:
                partner_source = self.env['res.partner'].search([('id', '=', partner_id)])
                # Merge dans SmartEco
                if hasattr(partner_source, 'tpa_membership_smarteco') and partner_source.tpa_membership_smarteco:
                    tpa_exernal_id = self.env['tpa.synchronization.status'].search(
                        [('ref_partner.id', '=', partner_id), ('tpa_name', '=', 'horanet_tpa_smarteco')])
                    partner_source.write({'tpa_membership_smarteco': False,
                                          'last_sync_date': datetime.datetime.now() + datetime.timedelta(minutes=1)})
                    if not fusion_smarteco:
                        dst_partner.write({'tpa_membership_smarteco': True})

                    tpa_exernal_id_dst = self.env['tpa.synchronization.status'].search(
                        [('ref_partner.id', '=', dst_partner.id), ('tpa_name', '=', 'horanet_tpa_smarteco')])
                    tpa_exernal_id_dst.action_synchronization_smarteco()
                    partner_dest_id = tpa_exernal_id_dst.external_id
                    partners_source_id = partners_source_id + str(tpa_exernal_id.external_id) + ","
                    data_merge = \
                        data_merge \
                        + partner_source.lastname \
                        + " " + partner_source.firstname \
                        + " de type " + partner_source.company_type \
                        + ", "
                    partner_source.delete_tpa_synchro_partner('horanet_tpa_smarteco', tpa_exernal_id.external_id)

        super(MergePartnerAutomatic, self)._merge(partner_ids, dst_partner)

        # appel de la fonction de fusion si les acteurs ont une synchronisation TPA
        if partners_source_id != "":
            self._merge_tpa_smarteco(partner_dest_id, partners_source_id, data_merge, dst_partner)

    def _merge_tpa_smarteco(self, partner_dest_id, partners_source_id, data_merge, dst_partner):
        u"""Appeler la fonction de fusion si les acteurs ont une synchronisation TPA."""
        rec_merge = self.sudo().env['tpa.synchronization.merge'].create({
            'tpa_name': "horanet_tpa_smarteco",
            'external_id_src': partners_source_id,
            'external_id_dest': partner_dest_id,
            'ref_partner_dest': dst_partner.id,
            'data': unicode(data_merge)})
        rec_merge.smarteco_merge()
