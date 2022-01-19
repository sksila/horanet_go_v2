odoo.define('horanet_website_account.CompanyPage', function (require) {
    'use strict';

    var Class = require('web.Class');
    var base = require('web_editor.base');
    var hideBlockUI = require('horanet_website.commons').hideblock_ui;

    base.ready().then(function () {
        var selector = '.view_company';
        if ($(selector).length) {
            new View();
            hideBlockUI();
        }
    });

    var View = Class.extend({
        init: function () {
            // Création de l'accordéon
            var self = this;
            var $employeeAccordion = $('.employee_accordion');
            $employeeAccordion.accordion({
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
            $('button.remove_employee').on('click', function () {
                swal({
                    title: "Are you sure?",
                    text: 'You will not be able to recover this imaginary file!',
                    type: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#DD6B55',
                    confirmButtonText: 'Yes, delete it!',
                    closeOnConfirm: false,
                },
                function (employee) {
                    self.removeEmployee(employee);
                }
                );
            });
            // Open first member or self
            var listTab = $('div.employee_accordion > div');
            if (listTab.find("div[user_employee='True']").length) {
                // Tout fermer
                $employeeAccordion.accordion('option', {
                    active: false,
                });
                // Ouvrir la tab self
                $employeeAccordion.accordion(
                    'option',
                    'active',
                    listTab.index(listTab.find("div[user_employee='True']").parent())
                );
            }
        },
        removeEmployee: function () {
            swal("Deleted!", "Your imaginary file has been deleted.", 'success');
        },
    });
});
