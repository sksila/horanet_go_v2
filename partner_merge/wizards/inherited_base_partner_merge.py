# coding: utf8

import psycopg2

from odoo import models, api, fields
from odoo.tools import mute_logger


class MergePartnerAutomatic(models.TransientModel):
    # region Private attributes
    _inherit = 'base.partner.merge.automatic.wizard'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    group_by_birthdate_date = fields.Boolean(string='Partner age')
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def default_get(self, fields):
        """Override the function default_get to set by default the group_by_name and group_by_birthdate  at True."""
        res = super(MergePartnerAutomatic, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if self.env.context.get('active_model') == 'res.partner' and active_ids:
            res['state'] = 'selection'
            res['partner_ids'] = active_ids
            res['dst_partner_id'] = self._get_ordered_partner(active_ids)[-1].id

        # new code
        if self.env.context.get('duplicate') is True:
            res['group_by_name'] = True

        return res

    @api.model
    def _update_foreign_keys(self, src_partners, dst_partner):
        """We override the function to delete faulty rows when there is unicity.

        The original code deleted several rows
        based only on the value of one column. Here we delete the specific row (record_id).
        """
        # ---------------------------
        # THIS IS PART OF THE BASE CODE UNCHANGED
        # find the many2one relation to a partner
        relations = self._get_fk_on('res_partner')
        record_id = 0

        for table, column in relations:
            if 'base_partner_merge_' in table:  # ignore two tables
                continue

            # get list of columns of current table (exept the current fk column)
            query = "SELECT column_name FROM information_schema.columns WHERE table_name LIKE '%s'" % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            # do the update for the current table/column in SQL
            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }
            # --------------------------
            # NEW CODE
            if len(columns) > 1:
                # We select all the lines
                query = 'SELECT * FROM "%(table)s" WHERE %(column)s IN %%s' % query_dic
                self._cr.execute(query, (tuple(src_partners.ids),))
                # For each line, we execute an update
                for data in self._cr.fetchall():
                    try:
                        with mute_logger('odoo.sql_db'), self._cr.savepoint():
                            # This is the id of the record to delete if there is an error
                            record_id = data[0]
                            query = 'UPDATE "%(table)s" SET %(column)s = %%s WHERE %(column)s' \
                                    ' IN %%s AND "id" = %%s' % query_dic
                            self._cr.execute(query, (dst_partner.id, tuple(src_partners.ids), record_id,))
                    except psycopg2.Error:
                        # updating fails, most likely due to a violated unique constraint
                        # We delete only the faulty row
                        if record_id:
                            query = 'DELETE FROM %(table)s WHERE %(column)s IN %%s AND "id" = %%s' % query_dic
                            self._cr.execute(query, (tuple(src_partners.ids), record_id))
                            self._cr.commit()
                        # This was the previous code
                        # We delete all the rows base on the value of one column
                        else:
                            query = 'DELETE FROM %(table)s WHERE %(column)s IN %%s' % query_dic
                            self._cr.execute(query, (tuple(src_partners.ids),))
        # Super
        super(MergePartnerAutomatic, self)._update_foreign_keys(src_partners, dst_partner)

    def _merge(self, partner_ids, dst_partner=None):
        """Override _merge from crm to set the dst_partner as non duplicate."""
        super(MergePartnerAutomatic, self)._merge(partner_ids, dst_partner)

        if dst_partner:
            dst_partner.is_duplicated = False

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
