odoo.define('horanet_website_account.FoyerPage', function (require) {
    'use strict';

    var Class = require('web.Class');
    var base = require('web_editor.base');
    var hideblockUI = require('horanet_website.commons').hideblock_ui;

    base.ready().then(function () {
        var selector = '.view_foyer';
        if ($(selector).length) {
            new View();
            hideblockUI();
        }
    });

    var View = Class.extend({
        init: function () {
            // Création de l'accordéon
            var self = this;
            $('.member_accordion').accordion({
                heightStyle: 'content',
                collapsible: true,
                beforeActivate: function (event, ui) {
                    // The accordion believes a panel is being opened
                    var currHeader; var
                        currContent;
                    if (ui.newHeader[0]) {
                        currHeader = ui.newHeader;
                        currContent = currHeader.next('.ui-accordion-content');
                        // The accordion believes a panel is being closed
                    } else {
                        currHeader = ui.oldHeader;
                        currContent = currHeader.next('.ui-accordion-content');
                    }
                    // Since we've changed the default behavior, this detects the actual status
                    var isPanelSelected = currHeader.attr('aria-selected') === 'true';

                    // Toggle the panel's header
                    currHeader.toggleClass('ui-corner-all', isPanelSelected).toggleClass('accordion-header-active ui-state-active ui-corner-top', !isPanelSelected).attr('aria-selected', ((!isPanelSelected).toString()));

                    // Toggle the panel's icon
                    currHeader.children('.ui-icon').toggleClass('ui-icon-triangle-1-e', isPanelSelected).toggleClass('ui-icon-triangle-1-s', !isPanelSelected);

                    // Toggle the panel's content
                    currContent.toggleClass('accordion-content-active', !isPanelSelected);
                    if (isPanelSelected) {
                        currContent.slideUp();
                    } else {
                        currContent.slideDown();
                    }

                    return false; // Cancels the default action
                },
            });
            $('button.remove_member').on('click', function () {
                swal({
                    title: "Are you sure?",
                    text: "You will not be able to recover this imaginary file!",
                    type: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#DD6B55',
                    confirmButtonText: "Yes, delete it!",
                    closeOnConfirm: false,
                },
                function (member) {
                    self.removeMember(member);
                }
                );
            });
            // Open first member or self
            var listTab = $('div.member_accordion > div');
            if (listTab.find("div[user_member='True']").length) {
                // Tout fermer
                $('.member_accordion').accordion('option', {
                    active: false,
                });
                // Ouvrir la tab self
                $('.member_accordion').accordion(
                    'option',
                    'active',
                    listTab.index(listTab.find("div[user_member='True']").parent())
                );
            }
        },
        removeMember: function () {
            swal("Deleted!", "Your imaginary file has been deleted.", "success");
        },
    });
});
