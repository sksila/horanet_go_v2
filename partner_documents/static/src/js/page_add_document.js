odoo.define('partner_documents.add_documents', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var documentTechnicalName;
    base.ready().then(function () {
        if ($('.horanet_add_document').length) {
            var tmp = new addDocument();
            tmp.init().done(function () {
                // débloquer la vue à la fin du chargement (pas de chargement async de la page)
            });

            if ($('#add_document_form').length) {
                var exit = true;
                $('#add_document_form').on('submit', function () {
                    exit = false;
                });
                window.onbeforeunload = function () {
                    if ($("input[type='file'].file_input").first().val() && exit === true) {
                        return 'Are you sure you want to navigate away from this page?';
                    }
                };
            }

            if ($('#modal_add_document_form').length) {
                $("input[type='file'].file_input").first().removeAttr('required');

                $("#btnModalAddDocumentSave").click(function () {
                    // Getting form into Jquery Wrapper Instance to enable JQuery Functions on form
                    var form = $("#modal_add_document_form");

                    // Declaring new Form Data Instance from form (to get input files)
                    var formData = new FormData(form[0]);

                    // Serializing all For Input Values (not files!) in an Array Collection so that we can iterate this collection later.
                    var params = form.serializeArray();

                    //Now Looping the parameters for all form input fields and assigning them as Name Value pairs.
                    $(params).each(function (index, element) {
                        formData.append(element.name, element.value);
                    });

                    if (typeof(documentTechnicalName) !== "undefined") {
                        formData.append('document_type', documentTechnicalName);
                    }

                    formData.append('modal_call', true);

                    //disabling Submit Button so that user cannot press Submit Multiple times
                    var btn = $(this);
                    btn.prop("disabled", true);

                    $.ajax({
                        url: "/my/documents/add",
                        method: "POST",
                        data: formData,
                        contentType: false,
                        processData: false,
                        cache: false,
                        async: false,
                        success: function (response) {
                            $('#errors').html("");
                            $('#errors').removeClass("alert alert-danger");
                            // alert("Upload Completed");
                            // console.log(response);
                            btn.prop("disabled", false);

                            // Verify if there are errors
                            if ($(response).find('.error').length) {
                                $('#errors').addClass("alert alert-danger");
                                $(response).find('.error').each(function () {
                                    $(this).removeClass("label label-danger");
                                    $('#errors').append($(this));
                                    $('#errors').append('<br/>');
                                });
                            } else {
                                // On enlève tous les input file sauf le dernier, qu'on vide
                                $("input[type='file'].file_input").last().val('');
                                $("input[type='file'].file_input").not(":last").remove();

                                // Fermer la modale
                                $('#ModalDocument').modal('toggle');
                            }
                        },
                        error: function (xhr, error) {
                            if (xhr.status === 0) {
                                alert('You are offline!!\n Please Check Your Network.');
                            } else if (xhr.status === 404) {
                                alert('Requested URL not found.');
                            } else if (xhr.status === 500) {
                                alert('Internel Server Error.');
                            } else if (error === 'parsererror') {
                                alert('Error.\nParsing JSON Request failed.');
                            } else if (error === 'timeout') {
                                alert('Request Time out.');
                            } else {
                                alert('Unknow Error.\n' + xhr.responseText);
                            }
                        },

                    });
                });

                $('#ModalDocument').on('show.bs.modal', function (event) {
                    var button = $(event.relatedTarget); // Button that triggered the modal
                    documentTechnicalName = button.data('document-technical-name'); // Extract info from data-* attributes
                    var recipientId = button.attr('data-recipient-id');
                    var selectRecipientId = $(this).find(".modal-body select[name='recipient']");

                    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
                    if (typeof(documentTechnicalName) !== "undefined") {
                        $(this).find(".modal-body select[name='document_type']").val(documentTechnicalName);
                        $(this).find(".modal-body select[name='document_type']").prop('disabled', true);
                    }
                    // Dans le cas où on a un bénéficiaire de défini
                    if (recipientId !== "" && typeof(recipientId) !== "undefined") {
                        selectRecipientId.val(button.attr('data-recipient-id'));
                    } else {
                        // On sélectionne le premier de la liste, qui est normalement l'utilisateur
                        selectRecipientId[0].selectedIndex = 0;
                    }
                    // On nettoie la zone d'erreurs (en cas de rechargement)
                    $('#errors').html("");
                    $('#errors').removeClass("alert alert-danger");

                    // On enlève tous les input file sauf le dernier, qu'on vide
                    $("input[type='file'].file_input").last().val('');
                    $("input[type='file'].file_input").not(":last").remove();
                });
            }
        }
    });

    var addDocument = function () {
        var _isInit = false;
        // Fonction d'initialisation de la classe, appelle des fonction d'init du model/view/controller
        var _init = function () {
            return $.Deferred(function (deferred) {
                if (_isInit) {
                    deferred.resolve();
                } else {
                    _isInit = 'pending';

                    // Utiliser then si les initialisations doivent se faires à la chaîne
                    view._init().then(function () {
                        $.when(model._init(), controller._init()).done(
                            function () {
                                _isInit = true;
                                deferred.resolve();
                            }
                        );
                    });
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
            nbFileInputs: 0,
        };
        // Controller : manage all user actions and provide model data to the view
        var controller = {
            // Fonction d'initialisation du controller
            _init: function () {
                return $.Deferred(function (deferred) {
                    view.$addDocumentBtn.on('click', function () {
                        model.nbFileInputs += 1;

                        var newFileInput = view.$lastFileInput.clone();

                        newFileInput.val('');
                        newFileInput.removeAttr('required');
                        newFileInput.insertAfter(view.$lastFileInput);

                        view.$lastFileInput = newFileInput;
                    });
                    deferred.resolve();
                }).promise();
            },
            callback: {},
        };
        // View : Display model data and sends user actions to the controller
        var view = {
            // Fonction d'initialisation de la vue
            _init: function () {
                return $.Deferred(function (deferred) {
                    deferred.resolve();
                }).promise();
            },
            $lastFileInput: $("input[type='file'].file_input").first(),
            $addDocumentBtn: $('button.horanet_add_document_btn'),
        };

        return {
            controller: controller,
            init: _init,
        };
    };
});
