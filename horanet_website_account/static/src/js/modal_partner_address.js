odoo.define('horanet_website_account.ModalPartnerAddress', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var CreateMember = require('horanet_website_account.FoyerMemberPage');

    base.ready().then(function () {
        var $selector = $('div[name=modal_horanet_contact_details]');
        if ($selector.length) {
            new CreateMember.PageCreateMember($selector);
        }
    });
});
