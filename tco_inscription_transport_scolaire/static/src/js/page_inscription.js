odoo.define('tco_inscription_transport_scolaire.manage_inscription', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var core = require('web.core');
    var horanet = require('horanet_website.commons');

    base.ready().then(function () {
        if ($('.horanet_page_inscription').length) {
            // Creation of an instance of the class managing the page inscription
            var selector = '.horanet_page_inscription';
            var classCreateInscription = new createInscription(selector);
            classCreateInscription.init().done(function () {
                // débloquer la vue à la fin du chargement (pas de chargement async de la page)
            }).fail(function (err) {
                console.log(err);
            });
            horanet.hideblock_ui();

            var $schoolCycle = $('#school_cycle');
            var $schoolGrade = $('#school_grade');
            $schoolGrade.children('option').hide();
            $schoolGrade.children('option[school_cycle_id="' + $schoolCycle.val() + '"]').show();

            $schoolCycle.change(function () {
                $schoolGrade.children('option').removeAttr('selected');
                $schoolGrade.children('option').hide();
                $schoolGrade.children('option[school_cycle_id="' + $(this).val() + '"]').show();
                $schoolGrade.children(':visible').first().attr('selected', 'selected');
            });
        }
    });

    // Class de gestion de la page d'inscription : NOT A SINGLETON
    var createInscription = function (domScope) {
        // Dom scope if specify on class constructor, or no scope (all document)
        var _domScope = $(domScope || ':root');
        var _isInit = false;

        // Fonction d'initialisation de la classe, appelle des fonction d'init du model/view/controller
        var _init = function () {
            return $.Deferred(function (deferred) {
                if (_isInit) {
                    deferred.resolve();
                } else {
                    _isInit = 'pending';
                    // Utiliser then si les initialisations doivent se faires à la chaîne
                    $.when(view._init()).then(model._init).then(controller._init).done(
                        function () {
                            _isInit = true;
                            deferred.resolve();
                        }
                    );
                }
            }).promise();
        };

        // Model : represent the data
        var model = {
            // Fonction d'initialisation du model
            _init: function () {
                return $.Deferred(function (deferred) {
                    deferred.resolve();
                }).promise();
            },
            getRecipientId: function () {
                var value = view.$recipientId.val();
                if ($.isNumeric(value)) {
                    return parseInt(value);
                }
                return false;
            },
            getRecipientIsSelf: function () {
                return !!view.$recipientId.find('option:selected').attr('data-is_self');
            },
            getRecipientIsAls: function () {
                return !!view.$recipientId.find('option:selected').attr('data-is_als');
            },
            getRecipientIsAddressValid: function () {
                return !!view.$recipientId.find('option:selected').attr('data-address_valid');
            },
            getTypeEstablishmentSelected: function () {
                return view.$radioIsPublic.closest(':checked').val();
            },
        };
        // Controller : manage all user actions and provide model data to the view
        var controller = {
            // Fonction d'initialisation du controller
            _init: function () {
                return $.Deferred(function (deferred) {
                    // Méthode d'initialisation du controller (event binding)
                    view.$selectSchoolCycle.change(function () {
                        controller.onChangeSchoolCycle($(this).find('option:selected').val());
                    });
                    view.$recipientId.change(function () {
                        controller.onChangeRecipient();
                    });
                    view.$radioIsPublic.change(function () {
                        controller.onChangeTypeEstablishment($(this).val());
                    });
                    view.$isDerogation.change(function (event) {
                        controller.onChangeIsDerogation(event);
                    });
                    view.$isAutomaticPayment.change(function (event) {
                        controller.onChangeIsAutomaticPayment(event);
                    });
                    view.$submitValidate.click(function (event) {
                        controller.onSubmitValidate(event);
                    });
                    view.$submitDraft.click(function (event) {
                        controller.onSubmitDraft(event);
                    });
                    view.$messageMissingAddress.click(function (event) {
                        controller.onClickMessageEditAddress(event);
                    });
                    view.$acceptTermsConditions.on("change", function () {
                        view.$boutonValidateInscription.prop("disabled", !$(this).is(":checked"));
                    });
                    // Au rechargement de la page, on vérifie si la case est cochée
                    view.$boutonValidateInscription.prop("disabled", !$(view.$acceptTermsConditions).is(":checked"));
                    // Au chargement on initialise la valeur du bénéficiaire sur le bouton des documents
                    view.$ButtonDocumentSchoolCertificate.attr('data-recipient-id', view.$recipientId.val());

                    view.$isStudent.change(function () {
                        view.clear.establishment();
                        controller.onClickIsStudent();
                    });
                    // On désactive le titre de transport si on est étudiant lorsque 'lon arrive sur la page
                    // On retire la période de règlement mensuelle
                    // if ($('input[name="is_student"]:checked').val() === "true"){
                    //      view.$transport_titre.prop("disabled", true);
                    //      $("option[value='monthly']", view.$invoicePeriod).attr('disabled', true);
                    // }
                    deferred.resolve();
                }).promise();
            },
            callback: {
                autocompleteEstablishment: function (data) {
                    // callback de retour d'appel ajax d'autocomplete, réalise le mapping pour un select HTML
                    return (
                        $.map(data.result, function (elt) {
                            return {
                                'label': (elt.name + ((elt.city_name) ? ' - ' + elt.city_name : '')).substring(0, 50),
                                'value': elt.id,
                                'name': elt.name,
                            };
                        })
                    );
                },
            },
            onSubmitValidate: function (event) {
                // event lors du submit du formulaire en validation
                event.preventDefault();
                if (controller.checkRequiredFields() === true) {
                    var _t = core._t;
                    swal({
                        title: _t("Are you sure ?"),
                        text: _t("You will not be able to edit the inscription afterward !"),
                        type: "warning",
                        showCancelButton: true,
                        confirmButtonColor: "#428BCA",
                        confirmButtonText: _t("Yes, validate the inscription"),
                        cancelButtonText: _t("No"),
                        closeOnConfirm: true,
                        closeOnCancel: true,
                    }, function (isConfirm) {
                        if (isConfirm) {
                            controller.onConfirmSubmitValidate();
                        } else {
                            event.preventDefault();
                        }
                    });
                }
            },
            onSubmitDraft: function (event) {
                // event lors du submit du formulaire en mode brouillon
                event.preventDefault();
                if (controller.checkRequiredFields() === true) {
                    var _t = core._t;
                    swal({
                        title: _t("Draft saved"),
                        text: _t("You need to saved the inscription for it to be accepted "),
                        type: "success",
                    },
                    function () {
                        controller.onConfirmSubmitDraft();
                    });
                }
            },
            onConfirmSubmitDraft: function () {
                $.blockUI();
                view.$submitDraft.closest('form').submit();
            },
            onConfirmSubmitValidate: function () {
                $.blockUI();
                view.$validate.val(true);
                view.$submitValidate.closest('form').submit();
            },
            establishmentSelected: function (itemEstablishment, element) {
                var establishmentId = itemEstablishment.value;
                view.$establishmentId.val(establishmentId);
                var isDerogation = false;
                if (establishmentId) {
                    var fieldsetEstablishment = $(element).closest('fieldset');
                    try {
                        fieldsetEstablishment.block();
                        var recipientId = model.getRecipientId();
                        if (!recipientId) {
                            view.$recipientId.closest('.required').addClass('has-error');
                        } else {
                            // is_derogation = controller.get_is_derogation(establishment_id, recipient_id);
                        }
                    } finally {
                        fieldsetEstablishment.unblock();
                    }
                }
                if ($('input[name="is_student"]:checked').val() !== "true") {
                    view.$isDerogation.prop('checked', isDerogation);
                } else {
                    view.$isDerogation.prop('checked', false);
                }
                view.$isDerogation.change();
            },

            periodSelected: function (period) {
                view.$period.closest('.required').removeClass('has-error');
                view.$periodId.val(period.value);
            },
            onChangeTypeEstablishment: function () {
                //var selected = view.$select_establishment.data("autocomplete").selectedItem
                view.refreshAutocomplete(view.$select_establishment);
            },
            checkRequiredFields: function () {
                // Vérifie la présence des champs requis du model d'inscription, afficher un warning a l'itilisateur
                // et de change le style des champs manquants
                var _t = core._t;
                if (!view.$recipientId.val() || !view.$periodId.val()) {
                    if (!view.$recipientId.val()) {
                        view.$recipientId.closest('.required').addClass('has-error');
                    }
                    if (!view.$periodId.val()) {
                        view.$periodId.closest('.required').addClass('has-error');
                    }
                    swal({
                        title: _t("Missing field"),
                        text: _t("You need to complete the required fields to proceed"),
                        type: "warning",
                    },
                    function () {
                        $("html, body").animate({scrollTop: 0}, "slow");
                        return false;
                    });
                } else {
                    return true;
                }
            },
            onChangeIsDerogation: function (event) {
                if ($(event.target).is(':checked')) {
                    view.$panelDerogation.show("slide", {direction: "left"}, 300);
                } else {
                    view.$panelDerogation.hide("slide", {direction: "left"}, 300, function () {
                        view.$derogationType.val('').change();
                    });
                }
            },
            onChangeIsAutomaticPayment: function (event) {
                if ($(event.target).val()) {
                    view.$panelCompte.show("slide", {direction: "left"}, 300);
                } else {
                    view.$panelCompte.hide("slide", {direction: "left"}, 300, function () {
                        view.$selectCompteId.val('').change();
                    });
                }
            },
            onClickMessageEditAddress: function () {
                var url = null;
                if (model.getRecipientIsSelf()) {
                    url = "/my/account";
                } else {
                    url = "/edit/member/" + model.getRecipientId();
                }
                window.location.href = url;
            },
            onChangeSchoolCycle: function () {
                view.clear.establishment();
                //model.refresh_sectors_ids();
            },
            onChangeRecipient: function () {
                view.$recipientId.closest('.required').removeClass('has-error');
                view.setIsAls(model.getRecipientIsAls());
                view.refreshMissingAddress();
                view.clear.establishment();
                view.$ButtonDocumentSchoolCertificate.attr('data-recipient-id', view.$recipientId.val());
            },
            onClickIsStudent: function () {
                if ($('input[name="is_student"]:checked').val() === "true") {
                    view.$transportTitre.val('cool_plus');
                    view.$transportTitre.prop("disabled", !$(this).is(":checked"));
                    // $("option[value='monthly']", view.$invoicePeriod).attr('disabled', true);
                    view.$invoicePeriod.prop('selectedIndex', 0);
                } else {
                    view.$transportTitre.prop("disabled", false);
                    // $("option[value='monthly']", view.$invoicePeriod).attr('disabled', false);
                }
            },
        };
        // View : Display model data and sends user actions to the controller
        var view = {
            // Fonction d'initialisation de la vue
            _init: function () {
                return $.Deferred(function (deferred) {
                    var main = _domScope;
                    view._initSelector(main);
                    view._initAutocomplete();
                    deferred.resolve();
                }).promise();
            },
            _initSelector: function (main) {
                this.$main = main;
                this.$ButtonDocumentSchoolCertificate = main.find('button[name=ButtonDocumentSchoolCertificate]');
                this.$selectEstablishment = main.find('input[name=etablissement]');
                this.$establishmentId = main.find('input[name=school_establishment_id]');
                this.$recipientId = main.find('select[name=recipient_id]');
                this.$period = main.find('input[name=period]');
                this.$periodId = main.find('input[name=period_id]');
                this.$selectSchoolCycle = main.find('select[name=school_cycle]');
                this.$radioIsPublic = main.find('input[type=radio][name=is_public]');
                this.$isDerogation = main.find('input[type=checkbox][name=is_derogation]');
                this.$isAls = main.find('input[type=radio][name=is_als]');
                this.$panelDerogation = main.find('div[name=panel_derogation]');
                this.$isAutomaticPayment = main.find('input[type=radio][name=is_automatic_payment]');
                this.$panelCompte = main.find('div[name=panel_compte_id]');
                this.$selectCompteId = main.find('select[name=compte_id]');
                this.$derogationType = main.find('select[name=derogation_type]');
                this.$submitValidate = main.find('button[type=submit][name=submit_validate]');
                this.$submitDraft = main.find('button[type=submit][name=submit_draft]');
                this.$validate = main.find('input[name=validate]');
                this.$messageMissingAddress = main.find('div[name=message_missing_address]');
                this.$acceptTermsConditions = main.find('input[name=is_accepting_conditions]');
                this.$boutonValidateInscription = main.find('button[name=submit_validate]');
                this.$isStudent = main.find('input[name=is_student]');
                this.$transportTitre = main.find('select[name=transport_titre]');
                this.$invoicePeriod = main.find('select[name=invoice_period]');
            },
            _initAutocomplete: function () {
                // Code commun au autocomplete widget
                var defaultAutocomplete = {
                    minLength: 1,
                    open: function () {
                        $(this).removeClass("ui-corner-all").addClass("ui-corner-top");
                    },
                    close: function () {
                        $(this).removeClass("ui-corner-top").addClass("ui-corner-all");
                    },
                    focus: function (event, ui) {
                        event.preventDefault();
                        $(this).val(ui.item.label);
                    },
                };
                // Création establishment
                view.$selectEstablishment.autocomplete($.extend({}, defaultAutocomplete, {
                    source: function (request, response) {
                        var domain = [];
                        domain.push([ "name", "=ilike", "%" + request.term + "%" ]);
                        domain.push([ "is_public", "=", (model.getTypeEstablishmentSelected() === "public") ]);
                        domain.push([ "computed_school_cycle", "in", [view.$selectSchoolCycle.val() || null]]);
                        horanet.ajaxautocomplete(
                            "/horanet/search/establishments", {
                                'term': request.term,
                                'limit': 20,
                                'domain': domain,
                            },
                            response,
                            controller.callback.autocompleteEstablishment
                        );
                    },
                    select: function (event, ui) {
                        event.preventDefault();
                        $(this).val(ui.item.name);
                        controller.establishmentSelected(ui.item, $(this));
                    },
                    focus: function (event, ui) {
                        event.preventDefault();
                        $(this).val(ui.item.name);
                    },
                })).focus(function () {
                    //Use the below line instead of triggering keydown
                    $(this).data("uiAutocomplete").search($(this).val() || '%');
                });

                // Autocomplete period
                view.$period.autocomplete($.extend({}, defaultAutocomplete, {
                    source: function (request, response) {
                        var domain = [];

                        /* TODO domain pour ne pas pouvoir créer deux inscription sur les mêmes période (bénéficiaires)*/
                        horanet.ajaxautocomplete(
                            "/web/dataset/search_read",
                            {
                                'model': "tco.inscription.period",
                                'domain': domain,
                                'limit': 20,
                                'fields': ["name"],
                            },
                            response,
                            function (data) {
                                return ($.map(data.result.records, function (elt) {
                                    return {
                                        'label': elt.name,
                                        'value': elt.id,
                                    };
                                }));
                            }
                        );
                    },
                    select: function (event, ui) {
                        event.preventDefault();
                        $(this).val(ui.item.label);
                        controller.periodSelected(ui.item, $(this));
                    },
                })).focus(function () {
                    //Use the below line instead of triggering keydown
                    $(this).data("uiAutocomplete").search($(this).val() || '%');
                });
            },
            setIsAls: function (bool) {
                // Modifie la valeur du radio button is_als
                view.$isAls.val([(bool) ? 'true' : '']);
            },
            // Méthode générique de reset d'autocomplete
            refreshAutocomplete: function (autocomplete) {
                autocomplete.attr('value', '');
                // Création d'un objet dummy, pour permettre au select de l'autocomplete d'accéder au label
                $(autocomplete).data('uiAutocomplete')._trigger('select', {}, {item: {label: ''}});
            },
            clear: {
                establishment: function () {
                    view.refreshAutocomplete(view.$selectEstablishment);
                },
            },
            refreshMissingAddress: function () {
                console.log('refresh');
                if (model.getRecipientIsAddressValid()) {
                    view.$recipientId.closest('.required').removeClass('has-error');
                    view.$messageMissingAddress.hide("slide", {direction: 'down'}, 300);
                } else {
                    view.$recipientId.closest('.required').removeClass('has-error');
                    view.$messageMissingAddress.show("slide", {direction: 'up'}, 300);
                }
            },
        };

        return {
            controller: controller,
            init: _init,
        };
    };
});
