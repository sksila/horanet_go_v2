from collections import defaultdict
from odoo import models, api


class ToolFieldDirty(models.AbstractModel):
    """Tools.field.dirty model is meant to be inherited by any model.

    That needs to use the possibility for à field to be changed by its own bound onchange method.
    This beavior is obtain by flaggind the changed field as "dirty", ence the name of the model

    Inheriting classes are not required to implement any method, as the default implementation will work for any model.

    dirty field features can be controlled through context keys :

    - ``force_dirty``: in the context will trigger the dirty flag on a field

    exemple :
    '<field name="XXX" context="{'force_dirty':True}"></field>'
    """

    # region Private attributes
    _name = 'tools.field.dirty'
    _description = 'Field dirty'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # region CRUD (overrides)
    @api.multi
    def onchange(self, values, field_name, field_onchange):
        """Override of the base method :meth:`model.Model.onchange`.

        to add the possibility to force a field to be dirty

        A dirty field will be send to the view for update after an onchange
        event, to use this override the key 'force_dirty' must be added
        to the context.

        Use case : force a Many2one field to have a name for the selection
        drop-down different than it's regular name

        :param values: dictionary mapping field names to values, giving the
            current state of modification
        :param field_name: name of the modified field, or list of field
            names (in view order), or False
        :param field_onchange: dictionary mapping field names to their
            on_change attribute
        """
        res = super(ToolFieldDirty, self).onchange(values, field_name, field_onchange)
        context = self.env.context or {}
        if context.get('force_dirty') and values.get(field_name):
            # create a new record with values, and attach ``self`` to it
            with self.env.do_in_onchange():
                record = self.new(values)

                def dct_structure():
                    return defaultdict(dct_structure)
                names = dct_structure()
                onchange_tuple = self._fields[field_name].convert_to_onchange(record[field_name], self, names)
                res['value'].update({field_name: onchange_tuple})
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
