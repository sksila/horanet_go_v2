from datetime import datetime
from odoo import models
from odoo import api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class Lang(models.Model):
    """Class that inherit res.lang to add methods."""

    _inherit = 'res.lang'

    @staticmethod
    def _get_default_date_format():
        """Use as default date format the european format.

        :return: european date format
        """
        return '%d/%m/%Y'

    @api.model
    def get_universal_date_format(self):
        """Get an universal date format used by the clientside and the serverside.

        :return: 'dd/mm/yy'
        :rtype: string
        """
        date_format = self.get_date_format()
        universal_format = date_format.replace('%d', 'dd').replace('%m', 'mm').replace('%Y', 'yy')
        return universal_format

    @api.model
    def get_date_format(self):
        """Get the format of the date corresponding to the lang."""
        lang = self.env.context.get('lang')
        if not lang:
            lang = 'en_US'
        lang_rec = self.search([('code', '=', lang)])[0]
        return lang_rec.read(['date_format'])[0]['date_format']

    @api.model
    def format_date(self, date_to_format):
        """Format the date."""
        date_format = self.env.context.get('date_format')
        if not date_format:
            date_format = self.get_date_format()

        date_obj = datetime.strptime(
            date_to_format, DEFAULT_SERVER_DATE_FORMAT)
        return date_obj.strftime(date_format)
