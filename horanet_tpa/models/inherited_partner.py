import logging
import uuid

from odoo import models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Override partner model to add TPA methods."""

    # region Private attributes
    _inherit = 'res.partner'

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
    # endregion

    # region Actions
    def get_tpa_external_id(self, tpa_name):
        """Return the external id key related to the TPA.

        :param tpa_name: name of the TPA
        :return: the external id or False
        """
        self.ensure_one()
        result = False
        rec_ir_model_data = self.get_tpa_external_id_rec(tpa_name)
        if rec_ir_model_data:
            rec_ir_model_data.ensure_one()
            result = rec_ir_model_data.name
        return result

    def get_tpa_external_id_rec(self, tpa_name):
        """Return the ir_model_data record related to the TPA for this partner if it exists.

        :param tpa_name: name of the TPA
        :return: ir_model_data record related to the TPA or none if it doesn't exists
        """
        self.ensure_one()
        ir_model_data = self.sudo().env['ir.model.data']
        rec_ir_model_data = ir_model_data.search(
            [('module', '=', tpa_name),
             ('model', '=', self._name),
             ('res_id', '=', self.id)])
        if len(rec_ir_model_data) > 1:
            # Delete all external ID (except one), will cascade delete tpa_synchronization_status
            (rec_ir_model_data - rec_ir_model_data[0]).unlink()
        return rec_ir_model_data and rec_ir_model_data[0] or None

    def get_or_create_tpa_external_id_rec(self, tpa_name, external_id=None):
        """Get or create TPA external ID.

        :param tpa_name: name of the TPA
        :param external_id: optional: the external id to use (must be unique)
        :return: the partner record
        """
        self.ensure_one()
        rec_ir_model_data = self.get_tpa_external_id_rec(tpa_name)
        if not rec_ir_model_data:
            if not external_id:
                external_id = uuid.uuid1()
            ir_model_data = self.sudo().env['ir.model.data']
            rec_ir_model_data = ir_model_data.create({
                'module': tpa_name,
                'model': self._name,
                'res_id': self.id,
                'name': external_id,
                'noupdate': True
            })
        return rec_ir_model_data

    def delete_tpa_external_id_rec(self, tpa_name):
        """Get or create TPA external ID.

        :param tpa_name: name of the TPA
        :return: the partner record
        """
        self.ensure_one()
        rec_ir_model_data = self.get_tpa_external_id_rec(tpa_name)
        if rec_ir_model_data:
            rec_ir_model_data.unlink()

        return True

    def get_or_create_tpa_synchro_partner(self, tpa_name, external_id=None):
        """Get or create TPA synchronisation status.

        :param tpa_name: name of the TPA
        :param external_id: optional: the external id to use (must be unique)
        :return: the tpa.synchronization.status record related to the TPA/partner
        """
        self.ensure_one()
        tpa_sync_status = self.sudo().env['tpa.synchronization.status']
        rec_ir_model_data = self.get_or_create_tpa_external_id_rec(tpa_name, external_id)
        rec_tpa_sync_status = tpa_sync_status.search([('ir_model_data_id', '=', rec_ir_model_data.id)])
        if not rec_tpa_sync_status:
            rec_tpa_sync_status = tpa_sync_status.create({
                'tpa_name': tpa_name,
                'ref_partner': rec_ir_model_data.res_id,
                'ir_model_data_id': rec_ir_model_data.id,
            })
        else:
            rec_tpa_sync_status.ensure_one()
        return rec_tpa_sync_status

    def delete_tpa_synchro_partner(self, tpa_name, external_id):
        """Get or create TPA synchronisation status.

        :param tpa_name: name of the TPA
        :param external_id: the external id to use (must be unique)
        :return: the tpa.synchronization.status record related to the TPA/partner
        """
        self.ensure_one()
        tpa_sync_status = self.sudo().env['tpa.synchronization.status']
        rec_ir_model_data = self.get_or_create_tpa_external_id_rec(tpa_name, external_id)
        rec_tpa_sync_status = tpa_sync_status.search([('ir_model_data_id', '=', rec_ir_model_data.id)])
        if rec_tpa_sync_status:
            rec_tpa_sync_status.unlink()
        self.delete_tpa_external_id_rec(tpa_name)

    # endregion

    # region Model methods
    # endregion

    pass
