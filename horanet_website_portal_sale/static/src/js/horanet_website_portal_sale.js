odoo.define('horanet_website_portal_sale.pay_lines', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var horanet = require('horanet_website.commons');

    base.ready().then(function () {
        if ($('.horanet_my_home').length > 0) {
            // To show more invoices
            ShowMore();
            horanet.hideblock_ui();
        }
        if ($('.horanet_payment').length > 0) {
            payment();
            horanet.hideblock_ui();
        }
        if ($('.horanet_invoice').length > 0) {
            // For move lines
            var tmp3 = new invoice();
            tmp3.init().done(function () {
            });
            horanet.hideblock_ui();
        }
    });


    var ShowMore = function () {
        $('.o_my_show_more').on('click', function (ev) {
            ev.preventDefault();
            $(this).parents('table').find(".to_hide").toggleClass('hidden');
            $(this).find('span').toggleClass('hidden');
        });
    };

    var payment = function () {
        'use strict';

        var view = {
            $payment:    $('.o_website_payment_form'),
            $reference:  $('#reference'),
            $AcquirerId: $('#acquirer_id'),
            $action:     $('#action'),
            $InvoiceIds: $('#invoice_ids'),
            $InvoiceId:  $('#invoice_id'),
            $MoveLineId: $('#move_line_ids'),
            $amount:     $('#amount_total')
        };

        var initialisation = {
            init: function () {
                view.$payment.on("click", 'button[type="submit"],button[name="submit"]', function (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    var $form = view.$payment.children('form');
                    ajax.jsonRpc('/my/home/payment/transaction/', 'call', {
                        'acquirer_id':   parseInt(view.$AcquirerId.val()),
                        'reference':     view.$reference.val(),
                        'action':        view.$action.val(),
                        'invoice_ids':   view.$InvoiceIds.val(),
                        'invoice_id':    parseInt(view.$InvoiceId.val()),
                        'move_line_ids': view.$MoveLineId.val(),
                        'amount':        parseFloat(view.$amount.val())
                    }).then(function () {
                        $form.submit();
                    });
                });
            }
        };

        initialisation.init();
    };

    var invoice = function () {
        var _IsInit = false;
        // Fonction d'initialisation de la classe, appelle des fonction d'init du model/view/controller
        var _init = function () {
            return $.Deferred(function (deferred) {
                if (_IsInit) {
                    deferred.resolve();
                } else {
                    _IsInit = 'pending';

                    // Utiliser then si les initialisations doivent se faires à la chaîne
                    view._init().then(function () {
                        $.when(controller._init(), model._init()).done(
                            function () {
                                _IsInit = true;
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
            }
        };
        // Controller : manage all user actions and provide model data to the view
        var controller = {
            // Fonction d'initialisation du controller
            _init: function () {
                return $.Deferred(function (deferred) {
                    view.$BulkPayButton.on('click', function () {
                        var SelectedMoveLines = $.map($('table').find('tr:has(input[name="pay-checkbox"]:checked)'), function (element) {
                            return $(element).attr('data_id');
                        });

                        view.$MoveLineIds.val(SelectedMoveLines);
                        view.$BulkPaymentForm.submit();
                    });
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
                    view._InitSelectors();

                    view.$PayToggleButtons.bootstrapToggle({
                        onstyle: 'success',
                        width:   '100%',
                        height:  '32px',
                        on:      '<i class="fa fa-shopping-cart" aria-hidden="true"></i>',
                        off:     core._t('Pay')
                    });
                    deferred.resolve();
                }).promise();
            },
            _InitSelectors: function () {
                this.$PayToggleButtons = $('input[name="pay-checkbox"');
                this.$BulkPayButton =    $('.bulk-pay-button');
                this.$BulkPaymentForm =  $('#bulk-payment-form');
                this.$MoveLineIds =      $('input[name="move_line_ids"]');
            }
        };

        return {
            controller: controller,
            init:       _init
        };
    };
});
