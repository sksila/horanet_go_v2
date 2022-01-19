from odoo import api, models, fields
from odoo.tools import safe_eval


class CollectivityContactSettings(models.TransientModel):
    """Extend Collectivity settings to add windows service url and port."""

    _inherit = 'res.config.settings'

    identification_windows_service_port = fields.Char(
        string="Windows service port",
        help=("The port to use is the one of the machine that run "
              "the windows service on your local network.")
    )
    mapping_id = fields.Many2one(
        string="Waste site support mapping",
        comodel_name='partner.contact.identification.mapping',
        help=("Set this value to use as default mapping value when "
              "launching the creation medium wizard.")
    )
    medium_recto_image = fields.Binary(
        string="Image used as background for the recto side of the medium",
        help=("This image should have following dimensions: "
              "325px width, 204px height")
    )
    medium_verso_image = fields.Binary(
        string="Image used as background for the verso side of the medium",
        help=("This image should have following dimensions: "
              "325px width, 204px height")
    )

    @api.model
    def get_values(self):
        """Return default values for identification settings.

        This return default values for mapping_id and windows service port
        """
        res = super(CollectivityContactSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        iprop = self.env['ir.property']
        identification_windows_service_port = ICPSudo.get_param('partner_contact_identification.windows_service_port')
        mapping_id = safe_eval(ICPSudo.get_param('partner_contact_identification.default_mapping_id', 'False'))

        medium_recto_image = iprop.get('medium_recto_image', 'collectivity.config.settings')
        medium_verso_image = iprop.get('medium_verso_image', 'collectivity.config.settings')

        res.update(
            identification_windows_service_port=identification_windows_service_port,
            mapping_id=mapping_id,
            medium_recto_image=medium_recto_image,
            medium_verso_image=medium_verso_image,
        )
        return res

    @api.multi
    def set_values(self):
        """Set the URL and port of the windows service that allow medium handling."""
        super(CollectivityContactSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        iprop = self.env['ir.property']
        ICPSudo.set_param(
            'partner_contact_identification.windows_service_port',
            self.identification_windows_service_port
        )
        ICPSudo.set_param('partner_contact_identification.default_mapping_id', self.mapping_id.id)

        iprop.set_property_binary('medium_recto_image', self.medium_recto_image, self._name)
        iprop.set_property_binary('medium_verso_image', self.medium_verso_image, self._name)
