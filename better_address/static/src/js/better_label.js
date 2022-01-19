odoo.define('better_address', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');

    FormRenderer.include({
       _updateView: function () {
            this._super.apply(this, arguments)
            this.$el.find('.horanet_td_form_label').parents('td').addClass('o_td_label').css('width', '');
       },
    });
});
