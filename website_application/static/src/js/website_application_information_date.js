odoo.define('website_application.InformationDate', function (require) {
    var base = require('web_editor.base');
    var context = require('web_editor.context');
    var Class = require('web.Class');

    base.ready().then(function () {
        $( "input.input_date[type=text]" ).each(function(index) {
            console.log( index + ": " + $( this ).text() );
            new WebsiteApplicationDate($(this))
        });
    });

    var WebsiteApplicationDate = Class.extend({
        init: function ($selector) {
            this.$inputDate = $selector;

            // On charge les langues du datepicker
            horanet.load_datepicker_regional($);
            // Init du date_picker date de naissance
            var lang = context.get().lang;
            if (!(lang in $.datepicker.regional)) {
                // Si la langue n'est pas connue des langues régionales, rechercher la plus proche
                lang = (lang.substring(0, 2) in $.datepicker.regional) ? lang.substring(0, 2) : 'en-GB';
            }
            // On créer le date_picker
            this.$inputDate.datepicker($.extend($.datepicker.regional[lang], {
                changeMonth: true,
                changeYear: true,
                autoSize: true,
                yearRange: 'c-100:c',
                dateFormat: this.$inputDate.attr('data_date_format')
            }));
        }
    });

    return WebsiteApplicationDate;
});
