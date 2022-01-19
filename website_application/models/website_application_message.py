from odoo import models, fields, api


class WebsiteApplicationMessage(models.Model):
    """Class of the messages of applications. Messages, like a chat, for applications."""

    # region Private attributes
    _name = 'website.application.message'
    _order = 'id desc'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    user_id = fields.Many2one(string='From', comodel_name='res.users',
                              default=lambda self: self.env.user, required=True)
    application_id = fields.Many2one(string='Application', comodel_name='website.application', required=True,
                                     ondelete='cascade')
    submit_date = fields.Datetime(string='Submit date', default=fields.Datetime.now, required=True)
    text = fields.Text(string='Text')
    is_read = fields.Boolean(string='is read')

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """
        Mettre is_read en true si celui qui poste un message est différent de celui qui a créé la demande.

        Cela veut dire que c'est un agent en BO qui poste un message et donc on peut le mettre
        d'office en lu.
        """
        application = self.env['website.application'].browse(vals.get('application_id'))
        # On envoi un nouveau message à l'applicant
        if application.applicant_id:
            if vals.get('user_id') != application.applicant_id.id:
                vals['is_read'] = True
                template_id = self.env.ref('website_application.email_application_new_message')
                template_id.send_mail(application.id, force_send=True)
        return super(WebsiteApplicationMessage, self).create(vals)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
