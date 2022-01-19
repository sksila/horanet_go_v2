import logging
import random
import threading
import time

import psycopg2

import odoo
from odoo import models, fields, api
from odoo.tools import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class TPASynchronizationMerge(models.Model):
    """This class represent a model intended to merge a res.partner with a third party application."""

    # region Private attributes
    _name = 'tpa.synchronization.merge'
    # endregion

    # region Default methods

    # endregion

    # region Fields declaration
    tpa_name = fields.Char(string="TPA name", selection=[], required=True)
    external_id_src = fields.Char(string="TPA ID Source", required=True)
    external_id_dest = fields.Char(string="TPA ID Dest", required=True)
    ref_partner_dest = fields.Many2one(string="Partner recipient", comodel_name='res.partner', required=True)
    last_message_export = fields.Text(string="Export message")
    try_number = fields.Integer(string="Number of attempts of sending")
    data = fields.Char(string="Data merge", required=True)
    status_date = fields.Datetime(string="DateTime status", default=fields.Datetime.now)
    status = fields.Integer(string="Status")
    last_message_export = fields.Text(string="Export message")

    # endregion

    # region Fields method
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
