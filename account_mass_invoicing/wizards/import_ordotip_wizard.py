# -*- coding: utf-8 -*-

# 1 : imports of python lib
import tempfile
import base64
import re
import logging
# 2 :  imports of odoo
from odoo import models, fields, api, _


class WizardImportOrdotip(models.TransientModel):
    """Class of import ORDOTIP file."""

    # region Private attributes
    _name = 'wizard.import.ordotip'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    upload_file = fields.Binary(string="Upload File", required=True)
    file_name = fields.Char(string="File name", readonly=True)
    log_text = fields.Text(default="")
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def import_file(self):
        """This methode import file and extract data then call the methods responsible for updating.

        Bank account of the invoice subscription and refresh the interface of import.
        """
        self.ensure_one()
        temp_file = tempfile.TemporaryFile()
        temp_file.write(base64.decodestring(self.upload_file))
        temp_file.seek(0)
        self.log_text = ""
        list_logs = []

        for line in temp_file.readlines():
            if re.match("^06", line):
                iban = line[67:94]
                rum = line[201:236]
                result = self._update_subscription(rum, iban)
                list_logs.extend(result)

        self._set_log(list_logs)

        return self._refresh_wizard()

    # endregion

    # region Model methods
    def _update_subscription(self, rum, iban):
        """
        This method tries to update Bank account of the invoice subscription.

        :param rum: unique mandate reference.
        :param iban: account number.
        :return list_log : [(status, log),...]  to describe the update status.
        """
        mandate_id = self.env["account.banking.mandate"].search([
            ["unique_mandate_reference", "like", rum[1:-2]]], limit=1).id
        if not mandate_id:
            # si le mandate_id n'existe pas => ajouter dans l'messages d'erreur
            mesgs = _("No mandate found for unique mandate reference : %s.") % rum
            return [(logging.ERROR, mesgs)]
        else:
            invoice_id = self.env["account.invoice"].search([("mandate_id", '=', mandate_id)])
            # si le invoice_id n'existe pas => ajouter dans l'messages d'erreur
            if not invoice_id:
                mesgs = _("No invoice found for unique mandate reference :  %s.") % rum
                return [(logging.ERROR, mesgs)]
            else:
                partner_id = invoice_id.partner_id
                account_id = self.env["res.partner.bank"].search([["acc_number", '=', iban]], limit=1)
                if account_id:
                    #
                    if invoice_id.subscription_id.bank_account_id and \
                            invoice_id.subscription_id.bank_account_id == account_id:

                        result = [(logging.WARNING, _("Bank account of the invoice subscription already up to date.")),
                                  (logging.INFO, False)]
                        return result
                    if account_id.partner_id:
                        if account_id.partner_id.id != partner_id.id:
                            # si le account_id.partner_id != partner_id
                            # alors le compte est affecte a un autre partner_id
                            #  => ajouter dans l'messages d'erreur
                            mesgs = _("Bank account with this Account Number %s belong to another Customer.") % iban
                            return [(logging.ERROR, mesgs)]
                        else:
                            invoice_id.subscription_id.bank_account_id = account_id
                            return [(logging.INFO, False)]
                    else:
                        invoice_id.subscription_id.bank_account_id = account_id
                        result = [(logging.WARNING,
                                   _("Bank account with this Account Number %s does not belong to any Customer.")
                                   % iban),
                                  (logging.INFO, False)]
                        return result
                else:
                    account_id = self.env["res.partner.bank"].create({"partner_id": partner_id.id, "acc_number": iban})
                    invoice_id.subscription_id.bank_account_id = account_id
                    return [(logging.INFO, _("Successful creation of a bank account with IBAN %s for Customer %s ") % (
                        iban, partner_id.name))]

    def _set_log(self, list_of_logs):
        """
        This method takes the list of logs as args and set it as value of Field log_text.

        :param list_of_logs : list of [(status, log),...].
        """
        self.log_text += "<pre style='line-height: 2.1;'>"

        for (status, log) in list_of_logs:
            error_message = ""
            message_info = "<font color='green'><strong>INFO</strong></font> => {}\n"
            message_error = "<font color='red'><strong>ERROR</strong></font> => {}\n"
            message_warning = "<font color='Orange'><strong>WARNING</strong></font> => {}\n"

            if status == logging.INFO:
                if log:
                    error_message += message_info.format(log)
                error_message += message_info.format(_("Bank account of the invoice subscription is up to date."))
            elif status == logging.ERROR:
                error_message += message_error.format(log)
            elif status == logging.WARNING:
                error_message += message_warning.format(log)
            self.log_text += error_message

        self.log_text += "</pre>"

    @api.multi
    def _refresh_wizard(self):
        self.ensure_one()

        return {
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
    # endregion
