'use strict';
var horanet = horanet || {};
horanet.page = horanet.page || {};

(function () {
    // utiliser dom_ready.then pour gagner en perf si il n'y a n'y widget qweb ni traduction
    odoo.website.ready().then(function () {
        'use strict';
        odoo.website.if_dom_contains('CSS SELECTOR', function () {
            // Creation of an instance of the class managing the page inscription
            var tmp = new horanet.page.CLASSNAME();
            tmp.init().done(function () {
                // débloquer la vue à la fin du chargement (pas de chargement async de la page)
                horanet.hide_blockui();
            });
        });
    });
})();

horanet.page.CLASSNAME = function () {
    var _isInit = false;
    // Fonction d'initialisation de la classe, appelle des fonction d'init du model/view/controller
    var _init = function () {
        return $.Deferred(function (deferred) {
            if (_isInit) {
                deferred.resolve();
            } else {
                _isInit = 'pending';
                // Utiliser then si les initialisations doivent se faires à la chaîne
                $.when(view._init(), model._init(), controller._init()).done(
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
        }
    };
    // Controller : manage all user actions and provide model data to the view
    var controller = {
        // Fonction d'initialisation du controller
        _init: function () {
            return $.Deferred(function (deferred) {
                deferred.resolve();
            }).promise();
        },
        callback: {}
    };
    // View : Display model data and sends user actions to the controller
    var view = {
        // Fonction d'initialisation de la vue
        _init: function () {
            return $.Deferred(function (deferred) {
                deferred.resolve();
            }).promise();
        }
    };

    return {
        controller: controller,
        init:       _init
    };
};
