odoo.define('horanet_website_account.PartnerBirthdate', function (require) {
    var base = require('web_editor.base');
    var Class = require('web.Class');
    var context = require('web_editor.context');

    var PartnerBirthdate = Class.extend({
        init: function ($selector) {
            this.$inputBirthdate = $selector.find('input[name=birthdate_date]');

            // On charge les langues du datepicker
            horanet.load_datepicker_regional($);
            // Init du date_picker date de naissance
            var lang = context.get().lang;
            if (!(lang in $.datepicker.regional)) {
                // Si la langue n'est pas connue des langues régionales, rechercher la plus proche
                lang = (lang.substring(0, 2) in $.datepicker.regional) ? lang.substring(0, 2) : 'en-GB';
            }
            // On créer le date_picker
            this.$inputBirthdate.datepicker($.extend($.datepicker.regional[lang], {
                changeMonth: true,
                changeYear: true,
                autoSize: true,
                yearRange: 'c-100:c',
                dateFormat: this.$inputBirthdate.attr('data_date_format'),
            }));
        },
    });

    return PartnerBirthdate;
});
