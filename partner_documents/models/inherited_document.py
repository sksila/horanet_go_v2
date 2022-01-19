import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

DOC_STATUS = (
    ('to_check', 'To check'),
    ('valid', 'Validated'),
    ('rejected', 'Rejected'),
)


class Document(models.Model):
    # region Private attributes
    _name = 'ir.attachment'
    _inherit = ['ir.attachment']
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        required=False,
        store=True,
        readonly=False
    )
    document_type_id = fields.Many2one(
        string="Document Type",
        comodel_name='ir.attachment.type'
    )
    status = fields.Selection(
        string="Status",
        selection=DOC_STATUS,
        readonly=True,
        default='to_check'
    )
    document_date = fields.Date(
        string="Document date",
        default=fields.Date.context_today
    )
    expiry_date = fields.Date(
        string="Expiration date",
        compute='_compute_expiry_date',
        readonly=False,
        store=True
    )
    is_expired = fields.Boolean(
        string="Expired",
        default=False,
        compute='_compute_is_expired',
        search='_search_is_expired'
    )
    archived = fields.Boolean(string="Archived")
    checked_by = fields.Many2one(
        string="Checked by",
        comodel_name='res.users',
        oldname='validated_by',
        readonly=True
    )
    checked_on = fields.Datetime(
        string="Checked on",
        oldname='validated_on',
        readonly=True)
    child_ids = fields.Many2many(
        string="Additionals pages",
        comodel_name='ir.attachment',
        relation='ir_attachment_recursive_rel',
        column1='child_ids',
        column2='parent_doc_id'
    )
    parent_doc_id = fields.Many2one(
        string="Document",
        comodel_name='ir.attachment',
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name='res.partner'
    )
    user_id = fields.Many2one(
        string="Owner",
        comodel_name='res.users'
    )
    number_of_files = fields.Integer(
        string="Number of files",
        compute='_compute_number_of_files',
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('status')
    def _compute_expiry_date(self):
        """Compute the expiry date of a document if its type have a validity period."""
        for rec in self:
            if rec.status == 'to_check':
                continue
            if not rec.document_date:
                rec.document_date = fields.Date.today()
            if rec.document_type_id.validity_period:
                rec.expiry_date = \
                    fields.Datetime.from_string(fields.Datetime.now()) \
                    + timedelta(days=rec.document_type_id.validity_period)

    @api.multi
    @api.depends('expiry_date')
    def _compute_is_expired(self):
        """Check if the document is expired corresponding to its expiry date and the current date."""
        for rec in self:
            if rec.expiry_date and rec.expiry_date < fields.Date.today():
                rec.is_expired = True

    @api.model
    def _search_is_expired(self, operator, value):
        """Recherche des document avec une date non expirée.

        - si pas de date => non expiré
        - si expiration à la date du jour => expiré

        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the `expiry_date` field
        """
        search_domain = ['|', ('expiry_date', '=', False), ('expiry_date', '>', fields.Date.today())]
        # en cas de recherche inverse, inverser le domain (exemple '!=' de False) avec un XOR
        if bool(operator in expression.NEGATIVE_TERM_OPERATORS) != bool(value):
            search_domain = [expression.NOT_OPERATOR] + search_domain

        return expression.normalize_domain(search_domain)

    @api.depends('child_ids')
    def _compute_number_of_files(self):
        """Compute the number of files (1 is for the initial file = datas)."""
        for rec in self:
            number_of_files = 1
            if rec.child_ids:
                number_of_files += len(rec.child_ids)
            rec.number_of_files = number_of_files

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('document_date', 'expiry_date')
    def _check_expiry_date(self):
        """Prevents saving date that are not consistent.

        :raise: odoo.exceptions.ValidationError if the document date is
            later than the expiry date
        :raise: odoo.exceptions.ValidationError if the expiry date is
            prior to the current date
        """
        for rec in self:
            if rec.document_date and rec.expiry_date and rec.document_date > rec.expiry_date:
                raise ValidationError(_("The document date cannot be set after expiration's date."))

            if rec.expiry_date and rec.expiry_date < fields.Date.today():
                raise ValidationError(_("The expiration date cannot be set before today's date."))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, values):
        """Override create method to be able to set parent values to its childs and set the name."""
        if not values.get('name', False):
            if not values.get('parent_doc_id', False):
                partner_name = self.env['res.partner'].browse(values.get('partner_id', False)).display_name or ''
                type_name = self.env['ir.attachment.type'].browse(values.get('document_type_id', False)).name or ''

                name = '{} - {}'.format(partner_name, type_name)
                values['name'] = name
        res = super(Document, self).create(values)
        res.set_child_ids_parent_values()
        return res

    @api.multi
    def write(self, values):
        """Override write method to be able to set parent values to its childs."""
        res = super(Document, self).write(values)
        self.set_child_ids_parent_values()
        return res

    @api.multi
    def set_child_ids_parent_values(self):
        """For each child of a document, set it its parent values."""
        for rec in self:
            if not rec.child_ids:
                continue

            for child_id in rec.child_ids:
                child_id.write({
                    'user_id': rec.user_id.id or None,
                    'partner_id': rec.partner_id.id or None,
                    'parent_doc_id': rec.id
                })
                child_id.name = child_id.datas_fname

    # endregion

    # region Actions
    @api.multi
    def change_status(self, status):
        """Change status of a document, also set by who and when if it's valid.

        :param status: status of the document to set
        """
        for rec in self:
            rec.status = status

            if status != 'to_check':
                rec.checked_by = self.env.user.id
                rec.checked_on = fields.Datetime.now()

        # On ne recharge la page que si on est sur un record existant
        if not self.env.context.get('no_reload', False):
            return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.multi
    def action_see_doc(self):
        """Open a new tab to visualize the content of the datas field."""
        if self.datas:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            return {
                "type": "ir.actions.act_url",
                "url": base_url + '/web/content/%s/%s' % (self.id, self.datas_fname),
                "target": "new",
            }

    # endregion

    # region Model methods
    @api.model
    def cron_delete_old_documents(self, number_of_days=365):
        """Cron that delete documents older than a certain number of days (default 365)."""
        _logger.info("Cron deleting old documents")
        old_documents = self
        domain = []

        # Documents périmés qui ont une date d'expiration.
        domain.extend(['&', ('expiry_date', '!=', False), ('expiry_date', '<', fields.Date.today())])
        # Documents qui n'ont pas de date d'expiration
        if int(number_of_days):
            param_date = fields.Date.from_string(fields.Date.today()) - timedelta(days=int(number_of_days))
            domain = expression.OR([domain,
                                    ['&', ('expiry_date', '=', False),
                                     ('document_date', '<', fields.Datetime.to_string(param_date))]])

        # Que les documents non admin
        domain = expression.AND([domain, [('user_id', '!=', 1)]])

        old_documents = self.search(domain)

        # Liste des fichiers dans les documents
        to_delete = set(attach.store_fname for attach in old_documents if attach.store_fname)
        # On vide l'emplacement dans le filestore dans les champs
        for old_document in old_documents:
            if old_document.store_fname:
                old_document.datas = False
                old_document.datas_fname = False
                old_document.store_fname = False
            if old_document.child_ids:
                for d in old_document.child_ids:
                    d.datas = False
                    d.datas_fname = False
                    d.store_fname = False
        for file_path in to_delete:
            # On marque les fichiers à supprimer
            self._file_delete(file_path)

        _logger.info("End of cron deleting old documents")

    # endregion

    pass
