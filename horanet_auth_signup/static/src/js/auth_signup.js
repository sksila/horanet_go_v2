odoo.define('horanet_auth_signup.signup', function (require) {
    'use strict';

    var hideBlockUi = require('horanet_website.commons').hideblock_ui;
    var Class = require('web.Class');
    var base = require('web_editor.base');
    var core = require('web.core');
    var _t = core._t;

    base.ready().then(function () {
        // Test si l'on est sur l'une des pages de gestion de login (signup/password/confirm/reset)
        if ($('div.oe_website_login_container').length > 0) {
            new ManageSignupForm();
        }
    });

    var ManageSignupForm = Class.extend({
        /**
         * Class de gestion des champ des formulaire 'signup' ET 'reset_password'
         */

        init: function () {
            var self = this;
            this.$radioIsCompany = $('input[name="is_company"]');
            this.$inputFirstname = $('input[name="firstname"]');
            this.$inputLastname = $('input[name="lastname"]');
            this.$inputName = $('input[name="name"]');
            this.$confirmLogin = $('input[name="confirm_login"]');
            this.$login = $('input[name="login"]');
            this.$password = $('#password');
            this.$confirmPassword = $('#confirm_password');

            this.$blocPartnerTitles = $('#bloc_partner_titles');
            this.$blocCompanyTitles = $('#bloc_company_titles');
            this.$blocName = this.$inputName.parent();
            this.$blocFirstname = $('#bloc_firstname');
            this.$blocLastname = $('#bloc_lastname');
            this.$labeLogin = $('label[for="login"]');

            // Bind view events
            this.$radioIsCompany.change(function () {
                self.onPartnerIsCompanyChange();
            });

            // Disable copy/paste (not if debug ;-)
            if (!window.location.search.match('debug=')) {
                this.disableCopy(this.$confirmLogin);
                this.disableCopy(this.$login);
                this.disableCopy(this.$password);
                this.disableCopy(this.$confirmPassword);
            }
            this.onPartnerIsCompanyChange();
            hideBlockUi();
        },

        disableCopy: function (element) {
            $(element).bind('paste', function (event) {
                event.preventDefault();
                swal({
                    icon: 'info',
                    title: _t("Information"),
                    allowOutsideClick: true,
                    text: _t("You cannot copy text in this field!"),
                });
                $(element).bind("contextmenu", function (event) {
                    event.preventDefault();
                });
            });
        },

        /**
         * Adapt fields displayed based on radio 'is company'
         */
        onPartnerIsCompanyChange: function () {
            var self = this;
            var isCompany = self.$radioIsCompany.filter(':checked').val() === 'True' || false;
            if (isCompany) {
                self.$blocCompanyTitles.show();
                self.$blocPartnerTitles.hide();

                self.$labeLogin.text(_t("Email"));
                self.$blocName.show();
                self.$inputName.prop('required', true);
                self.$blocFirstname.hide();
                self.$inputFirstname.prop('required', false);
                self.$blocLastname.hide();
                self.$inputLastname.prop('required', false);
            } else {
                self.$blocCompanyTitles.hide();
                self.$blocPartnerTitles.show();

                self.$labeLogin.text(_t("Your Email"));
                self.$blocName.hide();
                self.$inputName.prop('required', false);
                self.$blocFirstname.show();
                self.$inputFirstname.prop('required', true);
                self.$blocLastname.show();
                self.$inputLastname.prop('required', true);
            }
        },
    });
});
