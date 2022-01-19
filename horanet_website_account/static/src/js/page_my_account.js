odoo.define('horanet_website_account.AccountPage', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var Class = require('web.Class');

    var PartnerAddress = require('horanet_website_account.PartnerAddress');
    var PartnerImage = require('horanet_website_account.PartnerImage');
    var PartnerBirthdate = require('horanet_website_account.PartnerBirthdate');
    var PartnerPhone = require('horanet_website_account.PartnerPhone');
    var HideblockUi = require('horanet_website.commons').hideblock_ui;

    var textfill = require('horanet_website.commons').textfill;

    base.ready().then(function () {
        var $selector = $('div[name=horanet_my_account]');
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
            var $countryPhone = $('#country_phone');
            var $countryPhoneCode = $('#country_phone_code');
            var $countryMobile = $('#country_mobile');
            var $countryMobileCode = $('#country_mobile_code');
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
            new PartnerPhone($countryPhone, $countryPhoneCode, $countryMobile, $countryMobileCode);

            // Mise à l'échelle des textes
            this.ResizeTexte($selector);
            $(window).resize(function () {
                self.ResizeTexte();
            });
        },
        // Mise à l'échelle des textes
        ResizeTexte: function ($selector) {
            $selector.find('.horanet_textfill').each(function (i, elt) {
                textfill(elt, {
                    minFontPixels: 6,
                });
            });
        },
    });
});
