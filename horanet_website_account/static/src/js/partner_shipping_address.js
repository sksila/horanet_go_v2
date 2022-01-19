odoo.define('horanet_website_account.PartnerShippingAddress', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var PartnerAddress = require('horanet_website_account.PartnerAddress');

    base.ready().then(function () {
        var $selector = $('div[id=shipping_partner_address_form]');
        if ($selector.length) {
            var $zipcode = $('#shipping_zipcode');
            var $city = $('#shipping_city_id');
            var $cityID = $('#shipping_city');
            var $country = $('#shipping_country');
            var streetsRetrieved = null;
            var $streetID = $('#shipping_street_id');
            var $street = $('#shipping_street');
            var streetNumbersRetrieved = null;
            var $streetNumberID = $('#shipping_street_number_id');
            var $streetNumber = $('#shipping_street_number');
            var $additionalAddress = $('#shipping_additional_address1');
            var $additionalAddress2 = $('#shipping_additional_address2');
            var $createNewStreet = $('#shipping_create_new_street');
            var $newStreet = $('#shipping_new_street');
            var $inputNewStreet = $('#shipping_input_new_street');
            var $hasShippingAddress = $('input[name=has_shipping_address]');
            var $divNewStreet = $('div[id=shipping_new_street]');

            // Si on a coché la case adresse de facturation, on montre le formulaire, on active le champ zipcode
            var hasShippingAddressInputChange = function () {
                if ($hasShippingAddress.is(':checked')) {
                    $('div[id=shipping_partner_address_form]').show();
                    $zipcode.removeAttr('disabled');
                } else {
                    $zipcode.attr('disabled', 'disabled');
                }
            };

            hasShippingAddressInputChange();
            $hasShippingAddress.change(function () {
                hasShippingAddressInputChange();
            });

            new PartnerAddress($zipcode, $city, $cityID, $country, streetsRetrieved, $streetID, $street,
                streetNumbersRetrieved, $streetNumberID, $streetNumber, $additionalAddress,
                $additionalAddress2, $createNewStreet, $newStreet, $inputNewStreet, $divNewStreet);
        }
    });
});
