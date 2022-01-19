odoo.define('horanet_web.FormViewDialogWider', function (require) {
    'use strict';

    var Dialog = require('web.Dialog');

    Dialog.include({
        init: function () {
            this._super.apply(this, arguments);
            this._opened.done(function () {
                var class_selector = '.o-form-sheet-width-wider';
                if (this.$el.find(class_selector).addBack(class_selector)) {
                    this.$modal[0].firstElementChild.classList.add('o-modal-width-wider')
                }
            }.bind(this));
        }
    })
});
