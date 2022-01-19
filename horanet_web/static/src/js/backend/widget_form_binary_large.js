odoo.define('horanet_web.FieldBinaryFileLarge', function (require) {
    'use strict'

    var core = require('web.core')
    var registry = require('web.field_registry');
    var FieldBinaryFile = registry.get('binary')

    var FieldBinaryFileLarge = FieldBinaryFile.extend({
        template: 'FieldBinaryFile',

        init: function () {
            this._super.apply(this, arguments);
            this.max_upload_size = 250 * 1024 * 1024 // 250Mo
        }
    })

    core.form_widget_registry.add('bigfile_binary', FieldBinaryFileLarge)
});
