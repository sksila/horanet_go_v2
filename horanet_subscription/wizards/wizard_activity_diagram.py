import logging

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class WizardActivityDiagram(models.TransientModel):
    """Pseudo object, used to display a diagram view.

    When this object is creating, node and arrow object are created and linked to this 'activity.diagram'.
    The nodes and arrows are digram object created to transform the relation between activity.rules and
    activity.sector.

    All this is necessary to "cheat" the default diagram view, wich was designed to only work with two
    model (node and arrow), but the activity diagram has two node type (rules and sector) and no arrow
    """

    # region Private attributes
    _name = 'wizard.activity.diagram'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    nodes = fields.One2many(string="Nodes", comodel_name='wizard.activity.diagram.node',
                            inverse_name='diagram')

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Override to created all the mocking object for the diagram view representing the activity configuration."""
        diagram = super(WizardActivityDiagram, self).create(vals)
        node_model = self.env['wizard.activity.diagram.node']
        arrow_model = self.env['wizard.activity.diagram.arrow']
        activity_sectors = self.env['activity.sector'].search([])
        activity_rules = self.env['activity.rule'].search([])

        node_dictionary = {}
        for activity in activity_sectors:
            node_dictionary[activity] = node_model.create({
                'name': str(activity.code) + '\n' + str(activity.name),
                'diagram': diagram.id,
                'type': 'sector'
            })
        for rule in activity_rules:
            node_dictionary[rule] = node_model.create({
                'name': str(rule.code) + ' v' + str(rule.version) + '\n' + str(rule.name),
                'diagram': diagram.id,
                'type': 'rule'
            })
        for activity in activity_sectors:
            if activity.parent_id:
                arrow_model.create({
                    'label': 'Inherit sector activity' if activity.use_parent_activity else False,
                    'source': node_dictionary[activity].id,
                    'destination': node_dictionary[activity.parent_id].id
                })
        for rule in activity_rules:
            if rule.activity_sector_id:
                arrow_model.create({
                    'label': 'Priority ' + str(rule.priority),
                    'source': node_dictionary[rule].id,
                    'destination': node_dictionary[rule.activity_sector_id].id
                })
        return diagram

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_diagram_action_value(self):
        return {
            'name': _("Sector Diagram"),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'diagram',
            'res_id': self.id,
            'views': [(False, 'diagram')],
            'target': 'current',
        }

    # endregion
    pass


class WizardActivityNode(models.TransientModel):
    """Represent a node (activity.sector or activity.rule) in an activity diagram view."""

    # region Private attributes
    _name = 'wizard.activity.diagram.node'
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name")
    diagram = fields.Many2one(
        string="Diagram",
        comodel_name='wizard.activity.diagram')
    type = fields.Selection(
        string="Type",
        selection=[('sector', 'Sector'), ('rule', 'Rule')],
        required=True)
    incoming_arrow = fields.One2many(
        string="Incoming arrow",
        comodel_name='wizard.activity.diagram.arrow',
        inverse_name='destination')
    outgoing_arrow = fields.One2many(
        string="Outgoing arrow",
        comodel_name='wizard.activity.diagram.arrow',
        inverse_name='source')
    # endregion


class WizardActivityArrow(models.TransientModel):
    """Represent an arrow (relation between activity.sector and activity.rule) in an activity diagram view."""

    # region Private attributes
    _name = 'wizard.activity.diagram.arrow'
    _rec_name = 'label'
    # endregion

    # region Fields declaration
    source = fields.Many2one(
        string="Source",
        comodel_name='wizard.activity.diagram.node')
    destination = fields.Many2one(
        string="Destination",
        comodel_name='wizard.activity.diagram.node')
    label = fields.Char(
        string="Label")
    # endregion
