odoo.define('horanet_web.ButtonColumnRedirect', function (require) {
    'use strict'

    var core = require('web.core')
    var data = require('web.data')
    var session = require('web.session')

    var QWeb = core.qweb
    var Class = core.Class;
//    console.log('core:',core)
//    var Column = core.list_widget_registry.get('field') field key not exist in list_widget_registry.map in V11
    var Column = Class.extend({
        init: function (id, tag, attrs) {
            _.extend(attrs, {
                id: id,
                tag: tag
            });
            this.modifiers = attrs.modifiers ? JSON.parse(attrs.modifiers) : {};
            delete attrs.modifiers;
            _.extend(this, attrs);

            if (this.modifiers['tree_invisible']) {
                this.invisible = '1';
            } else { delete this.invisible; }
        },
        modifiers_for: function (fields) {
            var out = {};
            var domain_computer = data.compute_domain;

            for (var attr in this.modifiers) {
                if (!this.modifiers.hasOwnProperty(attr)) { continue; }
                var modifier = this.modifiers[attr];
                out[attr] = _.isBoolean(modifier)
                    ? modifier
                    : domain_computer(modifier, fields);
            }

            return out;
        },
        to_aggregate: function () {
            if (this.type !== 'integer' && this.type !== 'float' && this.type !== 'monetary') {
                return {};
            }

            var aggregation_func = (this.sum && 'sum') || (this.avg && 'avg') ||
                                   (this.max && 'max') || (this.min && 'min');

            if (!aggregation_func) {
                return {};
            }

            var C = function (fn, label) {
                this['function'] = fn;
                this.label = label;
            };
            C.prototype = this;
            return new C(aggregation_func, this[aggregation_func]);
        },
        heading: function () {
            return _.escape(this.string);
        },
        width: function () {},
        /**
         *
         * @param row_data record whose values should be displayed in the cell
         * @param {Object} [options]
         * @param {String} [options.value_if_empty=''] what to display if the field's value is ``false``
         * @param {Boolean} [options.process_modifiers=true] should the modifiers be computed ?
         * @param {String} [options.model] current record's model
         * @param {Number} [options.id] current record's id
         * @return {String}
         */
        format: function (row_data, options) {
            options = options || {};
            var attrs = {};
            if (options.process_modifiers !== false) {
                attrs = this.modifiers_for(row_data);
            }
            if (attrs.invisible) { return ''; }

            if (!row_data[this.id]) {
                return options.value_if_empty === undefined
                        ? ''
                        : options.value_if_empty;
            }
            var f = this._format(row_data, options);
            return (f !== '')? f : '&nbsp;';
        },
        /**
         * Method to override in order to provide alternative HTML content for the
         * cell. Column._format will simply call ``instance.web.format_value`` and
         * escape the output.
         *
         * The output of ``_format`` will *not* be escaped by ``format``, any
         * escaping *must be done* by ``format``.
         *
         * @private
         */
        _format: function (row_data, options) {
            return _.escape(formats.format_value(
                row_data[this.id].value, this, options.value_if_empty));
        }
    });
    var ColumnButtonRedirect = Column.extend({
        format: function (row_data, options) {
            options = options || {};
            var attrs = {};

            if (options.process_modifiers !== false) {
                attrs = this.modifiers_for(row_data);
            }

            if (attrs.invisible) { return ''; }

            this.icon = 'fa-external-link '

            return QWeb.render('ListView.row.button_redirect', {
                widget: this,
                prefix: session.prefix,
                disabled: attrs.readonly
                || isNaN(row_data.id.value)
                || data.BufferedDataSet.virtual_id_regex.test(row_data.id.value)
            });
        }
    })

    core.list_widget_registry.add('button.redirect', ColumnButtonRedirect);
});
