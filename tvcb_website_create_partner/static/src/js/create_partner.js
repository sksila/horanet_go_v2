odoo.define('tvcb_website_create_partner.create_partner', function (require) {
    'use strict';

    var base = require('web_editor.base');

    base.ready().then(function () {
        if ($('#tvcb_partner_form').length > 0) {
            new CreateNewPartner();
        }
    });

    var CreateNewPartner = function () {
        var ajaxSettings = {
            method: 'POST',
            contentType: 'application/json',
            async: true,
        };

        var $zipcode = $('#zipcode');
        var $city = $('#city');

        var retrieveCitiesByZipcode = function (zipcode) {
            var dfd = $.Deferred();

            $.ajax($.extend({}, ajaxSettings, {
                url: '/api/v1/public/horanet/address/city',
                data: JSON.stringify({
                    'params': {
                        'term': '%',
                        'zip_code': zipcode,
                        'limit': 1000,
                    },
                }),
            })).done(function (response) {
                dfd.resolve(response.result.records);
            });

            return dfd.promise();
        };

        var zipcodeInputChange = function () {
            if ($zipcode.val().length === 5) {
                $city.removeAttr('disabled');

                retrieveCitiesByZipcode($zipcode.val()).then(function (cities) {
                    $.each(cities, function () {
                        $city.append($("<option />").val(this.id).text(this.name));
                    });
                });
            } else {
                $city.attr('disabled', 'disabled');
                $city.find('option').filter(function () {
                    return $(this).val() !== '';
                }).remove();
                $city.change();
            }
        };

        zipcodeInputChange();
        $zipcode.on('input', zipcodeInputChange);

        $city.change(function () {
            if ($city.val() !== '') {
                $street.removeAttr('disabled');
                $streetNumber.removeAttr('disabled');
                $additionalAddress.removeAttr('disabled');
            } else {
                $street.attr('disabled', 'disabled');
                $streetNumber.attr('disabled', 'disabled');
                $additionalAddress.attr('disabled', 'disabled');
                $streetNumber.val('');
                $additionalAddress.val('');
                $street.val('');
                $streetID.val('');
            }
        });

        var retrieveStreetsByCity = function (streetName, cityID) {
            var dfd = $.Deferred();

            $.ajax($.extend({}, ajaxSettings, {
                url: '/api/v1/public/horanet/address/street',
                data: JSON.stringify({
                    'params': {
                        'term': streetName,
                        'city': parseInt(cityID),
                    },
                }),
            })).done(function (response) {
                dfd.resolve(response.result.records);
            });

            return dfd.promise();
        };

        var streetsRetrieved = null;
        var $streetID = $('#street_id');
        var $additionalAddress = $('#additional_address');

        var $street = $('#street').autocomplete({
            minLength: 3,
            delay: 500,
            source: function (request, response) {
                retrieveStreetsByCity(request.term, $city.val()).then(function (streets) {
                    streetsRetrieved = [];
                    $.each(streets, function () {
                        streetsRetrieved.push({'value': this.name,
                            'id': this.id});
                    });
                    response(streetsRetrieved);
                });
            },
            select: function (event, ui) {
                $.each(streetsRetrieved, function () {
                    if (this.value === ui.item.value) {
                        $streetID.val(this.id);
                    }
                });
            },
            focus: function (event, ui) {
                // On met un attribut sur l'élément surligné pour le reconnaître
                $(this).data('last_focused_element', ui.item);
                return false;
            },
            close: function () {
                // Si on ne sélectionne rien dans la liste, alors on vide le champs street_id
                if (!$(this).data('last_focused_element')) {
                    $streetID.val('');
                }
                // On réinitialise l'élément surligné
                $(this).removeData('last_focused_element');
            },
        });

        var retrieveStreetNumbers = function (number) {
            var dfd = $.Deferred();

            $.ajax($.extend({}, ajaxSettings, {
                url: '/public/horanet/address/street_number',
                data: JSON.stringify({'params': {'term': number}}),
            })).done(function (response) {
                dfd.resolve(response.result.records);
            });

            return dfd.promise();
        };

        var streetNumbersRetrieved = null;
        var $streetNumberID = $('#street_number_id');
        var $streetNumber = $('#street_number').autocomplete({
            minLength: 1,
            delay: 500,
            source: function (request, response) {
                retrieveStreetNumbers(request.term).then(function (streetNumbers) {
                    streetNumbersRetrieved = [];
                    $.each(streetNumbers, function () {
                        streetNumbersRetrieved.push({'value': this.name,
                            'id': this.id});
                    });
                    response(streetNumbersRetrieved);
                });
            },
            select: function (event, ui) {
                $.each(streetNumbersRetrieved, function () {
                    if (this.value === ui.item.value) {
                        $streetNumberID.val(this.id);
                    }
                });
            },
            focus: function (event, ui) {
                // On met un attribut sur l'élément surligné pour le reconnaître
                $(this).data('last_focused_element', ui.item);
                return false;
            },
            close: function () {
                // Si on ne sélectionne rien dans la liste, alors on vide le champs street_number_id
                if (!$(this).data('last_focused_element')) {
                    $streetNumberID.val('');
                }
                // On réinitialise l'élément surligné
                $(this).removeData('last_focused_element');
            },
        });

        $('#create_partner_form').submit(function () {
            $('#btn_submit').attr('disabled', 'disabled');
        });

        // Set the email required or not if checkbox is selected
        var $email = $('#email');
        var $emailLabel = $("label[for='" + $email.attr('id') + "']");

        var changeEmailRequiredAttribute = function () {
            if ($('#create_user').is(':checked')) {
                $email.attr('required', 'required');
                $emailLabel.text('* ' + $emailLabel.text().replace('* ', ''));
            } else {
                $email.removeAttr('required');
                $emailLabel.text($emailLabel.text().replace('* ', ''));
            }
        };

        changeEmailRequiredAttribute();
        $('#create_user').change(changeEmailRequiredAttribute);
    };

    return CreateNewPartner;
});
