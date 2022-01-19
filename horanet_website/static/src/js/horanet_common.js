odoo.define('horanet_website.commons', function (require) {
    'use strict';

    var base = require('web_editor.base');
    base.ready().then(function () {
        // Modification du composant blockUI pour l'ensemble du frontend
        if ($.blockUI) {
            $.blockUI.defaults.message = '<img src="/horanet_website/static/src/img/spinner-128.gif" style="width:18%"/>';
            $.blockUI.defaults.css = {
                padding: 0,
                margin: 0,
                width: '30%',
                top: '40%',
                left: '35%',
                textAlign: 'center',
                color: '#000',
                //border:         '3px solid #aaa',
                //backgroundColor:'#fff',
                cursor: 'wait'
            };
            $.blockUI.defaults.overlayCSS = {
                backgroundColor: 'rgba( 255, 255, 255)',
                opacity: 0.8,
                cursor: 'wait'
            }
        }
    });

    var hideblock_ui = function (options) {
        options = options || {};
        var mode = options.show && 'show' || 'hide';
        if ($('.horanet_blockui').length) {
            $('.horanet_blockui').each(function (i, element) {
                if (mode === 'show') {
                    $(element).show()
                } else {
                    $(element).hide()
                }
            })
        }
    };

    /**
     * Méthode de modification dynamique de la taille des textes pour s'adapter a la taille de l'élément parent
     * @param elt : l'élément sur lequel le texte doit être adapté
     * @param options
     * @returns {horanet.commons}
     */
    var textfill = function (elt, options) {
        // Si l'élément n'a pas de text, ne rien faire
        if (!$(elt).text()) return;
        // Encapsuler le contenu d'un span si il n'y en a pas
        if (!$(elt).children('span').length) {
            $(elt).wrapInner('<span />');
        }
        var minfontSize = options.minFontPixels || 4;
        var ourText = $('span:visible:first', elt);
        var maxHeight = $(elt).height();
        var maxWidth = $(elt).width();
        ourText.css('font-size', '');
        ourText.css('white-space', 'nowrap');
        var textHeight = ourText.height();
        var textWidth = ourText.width();
        // Si le texte est déjà à la bonne dimension, ne rien faire
        if (textHeight <= maxHeight && textWidth <= maxWidth) {
            return elt;
        }
        // pas besoin de tester plusieurs tailles, dans le cas d'un texte sur une ligne,
        // Un produit en croix permet de trouver immédiatement la bonne taille
        var fontSize = parseFloat(ourText.css('font-size'));
        var min_size = Math.min((fontSize * maxWidth / textWidth), (fontSize + maxHeight / textHeight));
        fontSize = Math.round(Math.max(minfontSize, min_size) * 100) / 100;
        ourText.css('font-size', fontSize);
        return elt;
    };

    var ajaxautocomplete = function (url, params, response_func, callBackSuccess, callBackError) {
        // Vérification de la présence des paramètres obligatoires
        if (!url) {
            throw "Paramètres manquant dans l'appel de la fonction HDCOM_functionCall"
        }
        // Appel de la méthode
        var response = $.ajax({
            type: "POST",
            url: url,
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
                'params': params
            }),
            cache: false,
            dataType: "json",
            success: function (msg, textStatus, jqXHR) {
                if (!!callBackSuccess) {
                    if (msg.error && msg.error.data && swal) {
                        jqXHR.error();
                        swal(msg.error.data.arguments[0] || 'Error', msg.error.data.arguments[1] || '', "error");
                    } else {
                        response_func(callBackSuccess(msg));
                    }
                }
            },
            error: function (error, exception) {
                if (typeof callBackError == 'function') {
                    callBackError(erreur, exception);
                } else if (error.status === 0) {
                    alert('Pas de connexion.\n Vérifiez le réseau.', "", "error");
                } else if (error.status == 404) {
                    alert('La page demandée n\'existe pas. [404]', "", "error");
                } else if (error.status == 500) {
                    alert('Internal Server Error [500].', "", "error");
                } else if (exception === 'parsererror') {
                    alert('Requested JSON parse failed.', "", "error");
                } else if (exception === 'timeout') {
                    alert('Time out error.', "", "error");
                } else if (exception === 'abort') {
                    alert('Ajax request aborted.', "", "error");
                } else {
                    alert('Erreur inattendue.\n' + error.responseText, "", "error");
                }
            },
            async: (!!callBackSuccess)
        });
        if (!callBackSuccess) return response;
    };

    return {
        'hideblock_ui': hideblock_ui,
        'textfill': textfill,
        'ajaxautocomplete': ajaxautocomplete
    }
});
