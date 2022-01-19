odoo.define('horanet_website_account.FoyerMemberPage', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var Class = require('web.Class');

    var PartnerAddress = require('horanet_website_account.PartnerAddress');
    var PartnerImage = require('horanet_website_account.PartnerImage');
    var PartnerBirthdate = require('horanet_website_account.PartnerBirthdate');

    var textfill = require('horanet_website.commons').textfill;
    var HideblockUi = require('horanet_website.commons').hideblock_ui;

    base.ready().then(function () {
        var $selector = $('div[name=horanet_contact_details]');
        if ($selector.length) {
            new View($selector);
            HideblockUi();
            $('#ButtonConfirm').on('click', function () {
                HideblockUi({show: true});
            });
        }
    });

    var View = Class.extend({
        init: function ($selector) {
            var self = this;
            var $zipcode = $('#zipcode');
            var $city = $('#city_id');
            var $cityID = $('#city');
            var $country = $('#country');
            var streetsRetrieved = null;
            var $streetID = $('#street_id');
            var $street = $('#street');
            var streetNumbersRetrieved = null;
            var $streetNumberID = $('#street_number_id');
            var $streetNumber = $('#street_number');
            var $additionalAddress = $('#additional_address1');
            var $additionalAddress2 = $('#additional_address2');
            var $createNewStreet = $('#create_new_street');
            var $newStreet = $('#new_street');
            var $inputNewStreet = $('#input_new_street');
            var $divNewStreet = $('div[id=new_street]');

            new PartnerAddress($zipcode, $city, $cityID, $country, streetsRetrieved, $streetID, $street,
                streetNumbersRetrieved, $streetNumberID, $streetNumber, $additionalAddress,
                $additionalAddress2, $createNewStreet, $newStreet, $inputNewStreet, $divNewStreet);
            new PartnerImage($selector.find('#partner_image'));
            new PartnerBirthdate($selector.find('#partner_birthdate'));

            // Mise à l'échelle des textes
            this._resizeText($selector);
            $(window).resize(function () {
                self._resizeText($selector);
            });
        },
        // Mise à l'échelle des textes
        _resizeText: function ($selector) {
            $selector.find('.horanet_textfill').each(function (i, elt) {
                textfill(elt, {
                    minFontPixels: 6,
                });
            });
        },
    });

    return {
        PageCreateMember: View,
    };
});
