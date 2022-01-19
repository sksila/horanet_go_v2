odoo.define('horanet_website_sale.payment', function (require) {
    "use strict";

    $(document).ready(function () {
        // Default check (or not) the terms checkbox from payment cart process
        var checkbox = $("#checkbox_cgv");
        var button = $("div.oe_sale_acquirer_button").find('button');
        if (checkbox.length > 0 && button.length > 0) {
            button.attr('disabled', 'disabled');
            if (checkbox.prop('checked')) {
                button.removeAttr('disabled');
            }
        }
    });
});
