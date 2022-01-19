odoo.define('horanet_website_account.PartnerAddress', function () {
    var PartnerAddress = function (
        $zipcode, $city, $cityID, $country, streetsRetrieved, $streetID, $street,
        streetNumbersRetrieved, $streetNumberID, $streetNumber, $additionalAddress,
        $additionalAddress2, $createNewStreet, $newStreet, $inputNewStreet, $divNewStreet) {
        // Déclaration des variables
        var ajaxSettings = {
            method: 'POST',
            contentType: 'application/json',
            async: true,
        };

        var createNewStreetInputChange = function () {
            // Si on a coché la case nouvelle rue, on active le nouveau champ, on vide le champ
            // street et on le désactive
            if ($createNewStreet.is(':checked') && $city.val()) {
                $street.attr('disabled', 'disabled');
                $street.val('');
                $streetID.val('');
                $inputNewStreet.removeAttr('disabled');
                $divNewStreet.show();
                $additionalAddress.removeAttr('disabled');
                $additionalAddress2.removeAttr('disabled');
            } else {
                $inputNewStreet.attr('disabled', 'disabled');
                $inputNewStreet.val('');
                // On ne réactive la rue que si il y a une ville
                if ($city.val()) {
                    $street.removeAttr('disabled');
                }
                // On ne désactive que les champs compléments que si la rue est vide
                if ($street.val() === '') {
                    $additionalAddress.attr('disabled', 'disabled');
                    $additionalAddress2.attr('disabled', 'disabled');
                }
            }
        };

        var disableAutocomplete = function myFunction () {
            if (navigator.userAgent.indexOf("Chrome") !== -1 ) {
                $streetNumber.attr('autocomplete', 'nope');
                $street.attr('autocomplete', 'nope');
            } else if (navigator.userAgent.indexOf("Firefox") !== -1 ) {
                $streetNumber.attr('autocomplete', 'off');
                $street.attr('autocomplete', 'off');
            } else {
                $streetNumber.attr('autocomplete', 'off');
                $street.attr('autocomplete', 'off');
            }
        };

        createNewStreetInputChange();
        $createNewStreet.change(function () {
            createNewStreetInputChange();
        });

        // On met à zéro le formulaire si on change de pays
        $country.change(function () {
            $zipcode.val('');
            $city.val('');
            $city.attr('disabled', 'disabled');
            $cityID.val('');
            $street.attr('disabled', 'disabled');
            $streetNumber.attr('disabled', 'disabled');
            $additionalAddress.attr('disabled', 'disabled');
            $additionalAddress2.attr('disabled', 'disabled');
            $inputNewStreet.attr('disabled', 'disabled');
            $streetNumber.val('');
            $additionalAddress.val('');
            $additionalAddress2.val('');
            $street.val('');
            $streetID.val('');
            $inputNewStreet.val('');
            $createNewStreet.attr('checked', false);
            $newStreet.hide();
        });

        var retrieveCitiesByZipcode = function (zipcode) {
            var dfd = $.Deferred();
            $.ajax($.extend({}, ajaxSettings, {
                url: '/api/v1/public/horanet/address/city',
                data: JSON.stringify({
                    'params': {
                        'term': '%',
                        'zip_code': zipcode,
                        'country_id': $country.val() ? parseInt($country.val()) : false,
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
                    // Automatic selection if only one city is available in cities list
                    if (cities.length === 1) {
                        $city.append($("<option selected />").val(cities[0].id).text(cities[0].name));
                        $city.change();
                    } else {
                        $.each(cities, function () {
                            // On pré-sélectionne la ville
                            if (this.id === parseInt($cityID.val())) {
                                $city.append($("<option selected />").val(this.id).text(this.name));
                            } else {
                                $city.append($("<option />").val(this.id).text(this.name));
                            }
                        });
                    }
                });
            } else {
                $city.attr('disabled', 'disabled');
                $cityID.val('');
                $city.find('option').filter(function () {
                    return $(this).val() !== '';
                }).remove();
                $city.change();
            }
        };

        zipcodeInputChange();
        $zipcode.on('input', zipcodeInputChange);

        $city.change(function () {
            $createNewStreet.prop('checked', false);
            $divNewStreet.hide();
            if ($city.val() !== '') {
                $street.removeAttr('disabled');
                $streetNumber.removeAttr('disabled');
                $streetNumber.val('');
                $streetNumberID.val('');
                $street.val('');
                $streetID.val('');
                $additionalAddress.val('');
                $additionalAddress2.val('');
            } else {
                $street.attr('disabled', 'disabled');
                $streetNumber.attr('disabled', 'disabled');
                $streetNumber.val('');
                $additionalAddress.val('');
                $additionalAddress2.val('');
                $street.val('');
                $streetID.val('');
            }
            streetInputChange();
            createNewStreetInputChange();
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

        var streetInputChange = function () {
            if ($street.val() !== '') {
                $additionalAddress.removeAttr('disabled');
                $additionalAddress2.removeAttr('disabled');
            } else {
                $additionalAddress.attr('disabled', 'disabled');
                $additionalAddress2.attr('disabled', 'disabled');
            }
        };

        $street.autocomplete({
            minLength: 3,
            delay: 500,
            source: function (request, response) {
                retrieveStreetsByCity(request.term, $city.val()).then(function (streets) {
                    streetsRetrieved = [];
                    $.each(streets, function () {
                        streetsRetrieved.push({
                            'value': this.name,
                            'id': this.id,
                        });
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
                streetInputChange();
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

        $streetNumber.autocomplete({
            minLength: 1,
            delay: 500,
            source: function (request, response) {
                retrieveStreetNumbers(request.term).then(function (streetNumbers) {
                    streetNumbersRetrieved = [];
                    $.each(streetNumbers, function () {
                        streetNumbersRetrieved.push({
                            'value': this.name,
                            'id': this.id,
                        });
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
        disableAutocomplete();
    };

    return PartnerAddress;
});
