from odoo import models, api


class IrActionsReport(models.Model):
    # region Private attributes
    _inherit = 'ir.actions.report'

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
    @api.model
    def _build_wkhtmltopdf_args(
            self,
            paperformat_id,
            landscape,
            specific_paperformat_args=None,
            set_viewport_size=False):
        """Override to add the viewport parameter to WkhtmlToPdf call if requested.

        The viewport is generated for the paper format and dpi used, this value allow report to be generated
        using template with relative element positioning (no dimensions)
        """
        command_args = super(IrActionsReport, self)._build_wkhtmltopdf_args(paperformat_id,
                                                                  landscape,
                                                                  specific_paperformat_args,
                                                                  set_viewport_size)

        if specific_paperformat_args and specific_paperformat_args.get('data-report-rectify-viewport'):
            if set(['--dpi', '--page-width', '--page-height']).issubset(command_args):
                # Get paper parameter
                arg_dpi = command_args[command_args.index('--dpi') + 1]
                arg_dpi = int(arg_dpi)
                arg_page_width = command_args[command_args.index('--page-width') + 1]
                arg_page_width = float(arg_page_width[:-2])
                arg_page_height = command_args[command_args.index('--page-height') + 1]
                arg_page_height = float(arg_page_height[:-2])

                # Create a viewport, corrected with WkhtmlToPdf dpi computation error
                magic_ratio = 1.25
                viewport_width = int(arg_page_width * arg_dpi / 25.4 * magic_ratio) - 1
                viewport_height = int(arg_page_height * arg_dpi / 25.4 * magic_ratio) - 1
                command_args.extend(['--viewport-size', str(viewport_width) + 'x' + str(viewport_height)])

        return command_args

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
