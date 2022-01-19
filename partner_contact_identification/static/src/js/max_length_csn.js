odoo.define('partner_contact_identification.max_length_csn', function (require) {
    'use strict';

    var FormRenderer = require('web.FormRenderer');
    var core = require('web.core');
    var _t = core._t;

    FormRenderer.include({
        confirmChange: function () {
            this.setMaxLengthOnCsnNumberInput()
            return  this._super.apply(this, arguments);
        },
        _renderView: function () {
            var self = this
            return this._super.apply(this, arguments).then(function(){
                 self.setMaxLengthOnCsnNumberInput();
            });
        },
        setMaxLengthOnCsnNumberInput : function () {
            console.log("setMaxLengthOnCsnNumberInput");
            this.$("table:has(label:contains('" + _t('Max length') + "'))").each(function (index, element) {
                var $maxLengthLabel = $($(element).find('label:contains("' + _t('Max length') + '")'));

                if ($maxLengthLabel.length > 0) {
                    var $maxLengthInput = $($maxLengthLabel[0].parentNode.nextSibling.firstChild);
                    var $csnNumberLabel = $($(element).find('label:contains("' + _t('CSN Number') + '")'));

                    if ($csnNumberLabel.length > 0) {
                        var $csnNumberInput = $($csnNumberLabel[0].parentNode.nextSibling.firstChild);
                        var $maxLengthInputNumber = $maxLengthInput.val() != "" ? $maxLengthInput.val() : $maxLengthInput.html()
                        $csnNumberInput.attr('maxlength', $maxLengthInputNumber);
                        $csnNumberInput.focus();
                    }
                }
            });
    },
    });
});
