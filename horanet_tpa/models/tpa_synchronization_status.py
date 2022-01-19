import logging
import random
import threading
import time

import psycopg2

import odoo
from odoo import models, fields, api
from odoo.tools import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class TPASynchronizationStatus(models.Model):
    """This class represent a model intended to synchronize a res.partner with a third party application."""

    # region Private attributes
    _name = 'tpa.synchronization.status'
    # endregion

    # region Default methods

    # endregion

    # region Fields declaration
    tpa_name = fields.Selection(string="TPA name", selection=[], required=True)
    ref_partner = fields.Many2one(string="Ref partner", comodel_name='res.partner', required=True,
                                  ondelete='cascade', help='partner-related data', delegate=False)
    ref_write_date = fields.Datetime(string="DateTime last partner update", default=fields.Datetime.now)
    last_sync_date = fields.Datetime(string="DateTime last synchronization")
    last_sync_try = fields.Datetime(string="DateTime last try of synchronization")
    ir_model_data_id = fields.Many2one(string="External ID", comodel_name="ir.model.data", required=True,
                                       ondelete='cascade')
    external_id = fields.Char(string="TPA ID", related='ir_model_data_id.name')
    last_message_export = fields.Text(string="Export message")
    is_up_to_date = fields.Boolean(
        string="Is up to date",
        compute='_compute_is_up_to_date',
        store=False,
        search='_search_is_up_to_date')
    try_number = fields.Integer(string="Number of tries since last export", default=0)

    # endregion

    # region Fields method
    @api.multi
    @api.depends('ref_write_date', 'last_sync_date')
    def _compute_is_up_to_date(self):
        for rec in self:
            rec.is_up_to_date = rec.ref_write_date <= (rec.last_sync_date or '')

    @api.model
    def _search_is_up_to_date(self, operator, value):
        """Search the Synchronization status which is up to date or not up to date."""
        if operator not in ['=', '!=']:
            raise NotImplementedError("Got operator '{operator}' (expected '=' or '!=')".format(operator=operator))
        status_ids = self.search([('last_sync_date', '!=', False)]).filtered(
            lambda sync_status: sync_status.ref_write_date <= sync_status.last_sync_date).ids
        # Cases ('is_up_to_date', '=', True) or ('is_up_to_date', '!=', False)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', status_ids)]
        else:
            return [('id', 'not in', status_ids)]

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def _lock_database_cursor(self, cursor):
        """Private method to get a locked database cursor.

        :return: Lock database cursor
        """
        # Define timeout at 30 seconds
        time_start = time.time()
        max_time = 30
        timeout_time = time_start + max_time

        cursor_locked = False

        while (not cursor_locked) and time.time() < timeout_time:
            try:
                # doc --> http://www.postgresql.org/docs/9.1/static/sql-select.html#SQL-FOR-UPDATE-SHARE
                cursor.execute("SELECT * FROM %s WHERE id = %s FOR SHARE NOWAIT" % (self._table, str(self.id)))
                cursor_locked = cursor.fetchone()
                if not cursor_locked:
                    cursor.rollback()
                    _logger.debug("Record already locked by another process/thread. waiting for it")
                else:
                    _logger.debug("Share lock acquired")
                    break
            except psycopg2.OperationalError as e:
                _logger.debug("Ignored PGSQL operational error: " + str(e).rstrip())
                _logger.debug("Rollback transaction, waiting to retry")
                cursor.rollback()
            time.sleep((random.randint(1000, 2000) / 1000.))

        if not cursor_locked:
            raise Warning("Couldn't acquired share lock in time, skipping the synchronization thread")

        return cursor

    def _thread_target(self, method_name):
        """Private method to call class method and manage database cursor.

        :param method_name: name of the class method to call
        :return: nothing
        """
        # Thread work properly for only one record
        self.ensure_one()

        # Set environment for this thread
        with odoo.api.Environment.manage():

            # Edit environment with new cursor
            lock_cr = self._lock_database_cursor(self.pool.cursor())
            lock_cr._default_log_exceptions = False
            self = self.with_env(self.env(cr=lock_cr, user=SUPERUSER_ID))

            try:
                # Search and call method by reflexion
                if hasattr(self, method_name):
                    # Limited time and number loop
                    try_count = 1
                    try:
                        method = getattr(self, method_name)
                        _logger.debug("Call of method %s in thread" % method_name)
                        method()
                        lock_cr.commit()
                        _logger.info("Thread synchronization completed")
                    except psycopg2.OperationalError as e:
                        _logger.debug("Ignored PGSQL operational error: " + str(e).rstrip())
                        time_start = time.time()
                        max_time = 30
                        timeout_time = time_start + max_time

                        while time.time() < timeout_time and try_count <= 5:
                            try_count += 1
                            try:
                                _logger.debug("Rollback transaction")
                                lock_cr.rollback()
                                time.sleep((random.randint(1000, 2000) / 1000.))
                                _logger.debug("Retry (%s) query : %s" % (try_count, str(lock_cr.query)))
                                # Execute request again
                                lock_cr.execute(lock_cr.query)
                                lock_cr.commit()
                                _logger.info("Thread synchronization completed")
                                break
                            except psycopg2.OperationalError as e:
                                _logger.debug("Ignored PGSQL operational error: " + str(e).rstrip())
                                continue

                        if time.time() >= timeout_time:
                            _logger.warning("Thread time out (%ss), abandon update of %s, id:%s"
                                            % (str(time.time() - time_start), self._name, self.id))
                        elif try_count > 5:
                            _logger.warning("Thread try attempts exceeded (%s), abandon update of %s, id:%s"
                                            % (str(try_count), self._name, self.id))
                else:
                    _logger.warning("Method `%s.%s` does not exist." % (self._name, method_name))
            except Warning as w:
                _logger.warning("Unexpected warning while processing thread job : " + str(w).rstrip())
            except Exception as e:
                _logger.warning("Unexpected exception while processing thread job : " + str(e))
                raise
            finally:
                lock_cr.close()
                _logger.debug("End of synchronization thread for method : %s" % method_name)

    @api.multi
    def execute_method_in_thread(self, method_name):
        """Asynchronous call of class method with its own cursor (lock).

        :param method_name: name of the class method to call
        :return: nothing
        """
        self.ensure_one()
        args = (method_name,)
        thread = threading.Thread(target=self._thread_target, args=args, name="Custom async cron for merge TPA")
        thread.start()
        _logger.debug("Thread started ! method: " + str(method_name))

    # endregion

    # endregion
    pass
