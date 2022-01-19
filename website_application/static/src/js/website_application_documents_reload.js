odoo.define('website_application.reload_documents', function (require) {
    'use strict';

    var base = require('web_editor.base');
    base.ready().then(function () {
        if ($('.horanet_add_document').length) {
            if ($('#modal_add_document_form').length) {
                $("#btnModalAddDocumentSave").click(function (event) {
                    var documentTypeTechnicalName = $('#modal_add_document_form').find(".modal-body select[name='document_type']").val();

                    // On compte le nombre de listes qui ont le même type de document
                    // (si plus d'un, on ne présélectionne pas la nouvelle pièce jointe)
                    var numberOfElementsWithTechnicalName = $("select[id^=document_selection][data-technical-name='" + documentTypeTechnicalName + "']").length;

                    // A la fermeture de la modale, on recharge la page pour récupérer le nouveaux documents éventuels
                    $.ajax({
                        url: "/my/documents/list",
                        method: "GET",
                        cache: false,
                        async: false,
                        success: function (response) {
                            if (typeof(response) !== 'undefined') {
                                // On parse la reponse pour récupérer la liste d'objets
                                var responseParsed = JSON.parse(response);

                                // Pour chaque élément de sélection de la page
                                $('select[id^=document_selection]').each(function (index, element) {
                                    // Type du document
                                    var idDocumentType = Number(element.dataset.documentTypeId);

                                    // Montrer les document//s existants
                                    var showExistingDocuments = element.dataset.showExistingDocuments;
                                    if (typeof(showExistingDocuments) === "undefined") { // Pour les templates utilisant la modale mais n'ayant pas défini ce paramètre
                                        showExistingDocuments = 'True';
                                    }

                                    // On récupère les ids des documents sélectionnés
                                    var value = $(element).val();
                                    if (value === null) {
                                        value = new Array();
                                    }

                                    // On vide la liste
                                    $(element).children().remove();

                                    // On la reremplit avec les documents récupérés
                                    var documents = new Array();
                                    responseParsed.forEach(function (document) {
                                        // qui correspondent au type de document de la liste
                                        if (document.document_type === idDocumentType) {
                                            documents.push(document);
                                        }
                                    });

                                    documents.forEach(function (document) {
                                        // tous ou (ceux déjà sélectionnés et celui qui vient d'être enregistré)
                                        if (showExistingDocuments === 'True' || value.indexOf(document.id.toString()) >= 0 ||
                                            (element.dataset.technicalName === documentTypeTechnicalName && document.id === documents[documents.length-1].id)) {
                                            var documentChildName = "";
                                            for (var i = 0; i < document.child_names.length; i++) {
                                                documentChildName += ', ' + document.child_names[i];
                                            }
                                            $(element).children().end().append('<option value="' + document.id +
                                                '" selected="post.get(\'document_' + document.document_type + ') == ' + document.id + '">' +
                                                document.name + ' (' + document.datas_fname + documentChildName + ')</option>');
                                        }
                                    });

                                    // On rajoute la valeur du dernier document enregistré dans value pour le sélectionner automatiquement
                                    // s'il n'y a qu'une seule liste pour le type de document sélectionné
                                    if (element.dataset.technicalName === documentTypeTechnicalName && numberOfElementsWithTechnicalName === 1) {
                                        value.push($(element).children().last().val());
                                        // On (re)attribut l'élément required pour internet explorer afin qu'il prenne en compte la pièce jointe
                                        $(element).attr("required", "required");
                                    }

                                    // On (re)sélectionne les valeurs
                                    $(element).val(value);
                                });
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
                        }

                    });
                });
            }
        }
    });
});
