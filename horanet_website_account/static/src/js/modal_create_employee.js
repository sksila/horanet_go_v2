odoo.define('horanet_website_account.create_employee', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var PartnerImage = require('horanet_website_account.PartnerImage');

    var createEmployee = function () {
        console.log("Début fonction createEmployee");

        var lastname = $('input[name="lastname"]');

        //      TODO Ajouter appel au nouveau controller

        console.log("Fin fonction createEmployee");

        $('select[name="recipient_id"]').prop('disabled', lastname.val().length !== 0);
    };

    base.ready().then(function () {
        var $selector = $('#ModalCreateEmployee');
        if ($selector.length) {
            console.log("Ok !");
            new PartnerImage($selector.find('#partner_image'));
            $('#btnCreateEmployee').click(createEmployee);
        }
    });
});