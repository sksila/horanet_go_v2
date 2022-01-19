odoo.define('horanet_website_sale.address', function (require) {
    "use strict";
    var PartnerAddress = require('horanet_website_account.PartnerAddress');

    $(document).ready(function () {
        if ($('form[name="/shop/checkout"]').length) {
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
            var $divNewStreet = $('#new_street');

            // Load PartnerAddress from horanet_website_account module on elements in shipping/billing cart
            new PartnerAddress($zipcode, $city, $cityID, $country, streetsRetrieved, $streetID, $street,
                streetNumbersRetrieved, $streetNumberID, $streetNumber, $additionalAddress,
                $additionalAddress2, $createNewStreet, $newStreet, $inputNewStreet, $divNewStreet);
        }
    });
});