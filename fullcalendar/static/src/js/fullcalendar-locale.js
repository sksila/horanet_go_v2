odoo.define('fullcalendar.locale', function (require) {
    'use strict';

    var base = require('web_editor.base');

    // Current language from context or HTML tag
    var currentLang = (base.get_context().lang || $('html').attr('lang')).replace('_', '-').toLowerCase();
    var currentLangArray = currentLang.split('-');

    (function ($) {
        if ($.fullCalendar) {
            // Get fullCalendar sources and version
            var fullCalendarMajorVersion = parseInt($.fullCalendar.version.split('.')[0]);
            var fullCalendar = $.fn.fullCalendar;

            $.fn.fullCalendar = function (params) {
	            var args = Array.prototype.slice.call(arguments, 1); // for a possible method call
                if (_.isObject(params)) {
                    // Locale param has been renamed from 'lang' to 'locale' in version 3
                    var localeParam = (fullCalendarMajorVersion < 3) ? 'lang' : 'locale';

                    // If locale param has not been set explicitly, set the same as HTML tag (from Odoo server)
                    if (!params[localeParam]) {
                        var locale = false;

                        // Available languages into FullCalendar plugin
                        var availableLangs = ['ar', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'es', 'eu', 'fa', 'fi', 'fr', 'gl', 'he',
                            'hi', 'hr', 'hu', 'id', 'in', 'is', 'it', 'iw', 'ja', 'ko', 'lb', 'lt', 'lv', 'nb', 'nl', 'nn',
                            'pl', 'pt-br', 'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tl', 'tr', 'uk', 'vi', 'zh-cn',
                            'zh-tw'
                        ];

                        switch (currentLangArray.length) {
                            case 2:
                                if ($.inArray(currentLang, availableLangs)) {
                                    locale = currentLang;
                                } else if ($.inArray(currentLangArray[0], availableLangs)) {
                                    locale = currentLangArray[0];
                                } else if ($.inArray(currentLangArray[1], availableLangs)) {
                                    locale = currentLangArray[1];
                                }
                                break;
                            default:
                                if ($.inArray(currentLangArray[0], availableLangs)) {
                                    locale = currentLangArray[0];
                                }
                        }

                        // Force locale parameter if corresponding locale has been reached into FullCalendar locales
                        if (!!locale) {
                            params[localeParam] = locale
                        }
                    }
                }

                // Apply default code from FullCalendar plugin
                fullCalendar.apply(this, [params, args[0]]);
            };
        }
    })(jQuery);
});