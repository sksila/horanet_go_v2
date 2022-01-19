odoo.define('horanet_website_account.PartnerInvoiceAddress', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var PartnerAddress = require('horanet_website_account.PartnerAddress');

    base.ready().then(function () {
        var $selector = $('div[id=invoice_partner_address_form]');
        if ($selector.length) {
            var $zipcode = $('#invoice_zipcode');
            var $city = $('#invoice_city_id');
            var $cityID = $('#invoice_city');
            var $country = $('#invoice_country');
            var streetsRetrieved = null;
            var $streetID = $('#invoice_street_id');
            var $street = $('#invoice_street');
            var streetNumbersRetrieved = null;
            var $streetNumberID = $('#invoice_street_number_id');
            var $streetNumber = $('#invoice_street_number');
            var $additionalAddress = $('#invoice_additional_address1');
            var $additionalAddress2 = $('#invoice_additional_address2');
            var $createNewStreet = $('#invoice_create_new_street');
            var $newStreet = $('#invoice_new_street');
            var $inputNewStreet = $('#invoice_input_new_street');
            var $hasInvoiceAddress = $('input[name=has_invoice_address]');
            var $divNewStreet = $('div[id=invoice_new_street]');

            // Si on a coché la case adresse de facturation, on montre le formulaire, on active le champ zipcode
            var hasInvoiceAddressInputChange = function () {
                if ($hasInvoiceAddress.is(':checked')) {
                    $('div[id=invoice_partner_address_form]').show();
                    $zipcode.removeAttr('disabled');
                } else {
                    $zipcode.attr('disabled', 'disabled');
                }
            };

            hasInvoiceAddressInputChange();
            $hasInvoiceAddress.change(function () {
                hasInvoiceAddressInputChange();
            });

            new PartnerAddress($zipcode, $city, $cityID, $country, streetsRetrieved, $streetID, $street,
                streetNumbersRetrieved, $streetNumberID, $streetNumber, $additionalAddress,
                $additionalAddress2, $createNewStreet, $newStreet, $inputNewStreet, $divNewStreet);
        }
    });
});
