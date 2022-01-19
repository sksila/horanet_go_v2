import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..config import config

_logger = logging.getLogger(__name__)
zip_import_count = 0


class HoranetZip(models.Model):
    """This model represent a postal code (ZIP code)."""

    # region Private attributes
    _name = "res.zip"
    _order = "name asc"
    _sql_constraints = [('unicity_code', 'UNIQUE(name)', _('The Zip value must be unique'))]
    # _rec_name = "display_name" #override by name_get
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    #  display_name = fields.Char('Name', compute='_get_display_name', store=True)
    name = fields.Char(srting='ZIP', size=20, help='The localized ZIP code', required=True)
    city_ids = fields.Many2many(string='Cities', comodel_name='res.city', required=True)
    state = fields.Selection(string='Status', selection=config.STATES_LIST, default='draft')

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('name')
    def onchange_name(self):
        """Check if the zip is already exists.

        :raise ValidationError: if the zip code already exist
        """
        for rec in self:
            if rec.name:
                if bool(rec.id):
                    duplicate_zip = rec.search(args=[('name', '=', rec.name), ('id', '!=', rec.id)], limit=1)
                else:
                    duplicate_zip = rec.search(args=[('name', '=', rec.name)], limit=1)
                if len(duplicate_zip) > 0:
                    raise ValidationError(_("The ZIP code already exist"))
                    # endregion

                    # region CRUD (overrides)

    @api.model
    def create(self, vals):
        """Override create method to print a log when importing and set them to confirmed.

        If the state is not specified.
        """
        context = self.env.context or {}
        if context.get('install_mode'):
            # install_mode : semble être l'équivalent du mode de création par import
            if context.get('trace_progression') and context.get('nb_rec'):
                global zip_import_count
                zip_import_count += 1
                # self.env.context = self.with_context(nb_rec_done=(nb_done + 1)).env.context
                # self.env.nb_rec_done = self.env.nb_rec_done + 1 if hasattr(self.env, 'nb_rec_done') else 1
                if (zip_import_count % 100) == 0:
                    _logger.info("Processing record {0} of {1}".format(zip_import_count, context.get('nb_rec')))
            if 'state' not in vals:
                vals['state'] = 'confirmed'
        return super(HoranetZip, self).create(vals)

    @api.model
    def load(self, import_fields, data):
        """Wrapper for the load method.

        It ensures that all valid records are loaded, while records that can't be loaded
        for any reason are left out.
        Returns the failed records ids and error messages.
        """
        if len(data) > 0:
            debug = self.env.ref('base.group_no_one') in self.env.user.groups_id
            global zip_import_count
            zip_import_count = 0
            return super(HoranetZip, self.with_context(nb_rec=len(data), trace_progression=debug)).load(
                import_fields, data)
        return super(HoranetZip, self).load(import_fields, data)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search a zip that 'start with'."""
        args = list(args or [])
        # Ignorer les argument de recherche si il n'y a pas de ville jointe dans le cas d'un many2many avec '=?'
        if len(args) == 1 and len(args[0]) == 3 \
                and args[0][0] == 'city_ids' and args[0][1] == '=?' and args[0][2] is False:
            args = []
        filter_by_name = [('name', '=ilike', name + '%')]
        res = self.search_read(filter_by_name + args, ['name'], limit=limit)
        return [(r['id'], r['name']) for r in res]

    # endregion

    # region Actions
    @api.multi
    def action_draft(self):
        """Set the zip state to draft."""
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        """Set the zip state to confirmed."""
        self.ensure_one()
        self.state = 'confirmed'

    @api.multi
    def action_invalidate(self):
        """Set the zip state to invalidated."""
        self.ensure_one()
        self.state = 'invalidated'

    # endregion

    # region Model methods
    # endregion
    pass
