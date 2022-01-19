odoo.define('partner_contact_identification.medium_handler', function (require) {
    'use strict';

    var FormRenderer = require('web.FormRenderer');
    var rpc = require('web.rpc');

    var core = require('web.core');
    var framework = require('web.framework');

    var _t = core._t;

    var controller = {
        callback: {
            ajaxSuccess: function (response) {
                var data = response.readResult || response.writeResult || response.formatResult;

                if (response.readResult) view.displayInformations('read', data);
                if (response.writeResult) view.displayInformations('write', data);
                if (response.formatResult) view.displayInformations('format', data);
            },
            ajaxError: function (response) {
                framework.unblockUI();

                view.$readErrorDiv.removeClass('hide');

                if (response.statusText === 'timeout') {
                    view.$readErrorDiv.text(_t('The windows service is not responding.'));
                } else if (response.state() === 'rejected') {
                    view.$readErrorDiv.text(_t('The windows service is not reachable at this address: ') + model.baseUrl);
                } else {
                    view.$readErrorDiv.text(response.statusText);
                }
            },
        },
        readMedium: function () {
            var method = 'read';
            var args = {
                id: model.transactionId,
            };

            $.ajax($.extend({}, model.settings, {
                url:  model.baseUrl + '/' + method,
                data: JSON.stringify(args),
            })).done(controller.callback.ajaxSuccess).fail(controller.callback.ajaxError);
        },
        formatMedium: function () {
            var method = 'format';
            var args = {
                id: model.transactionId,
            };

            $.ajax($.extend({}, model.settings, {
                url:  model.baseUrl + '/' + method,
                data: JSON.stringify(args),
            })).done(controller.callback.ajaxSuccess).fail(controller.callback.ajaxError);
        },
        writeMedium: function (context) {
         $.when(
             model.call_method({
                        model: model.partnerObj,
                        method: 'search_read',
                        domain: [ [ 'id', '=', context.default_reference_id ] ]
                    }),
             model.call_method({
                        model: model.wizardObj,
                        method: 'get_or_create_tag',
                        args: [ 'h3' ]
                    })
            ).done(function (partners, tags) {
                model.partner = partners[0];
                model.tag = tags[0];

                // The tag length is now 20 digits but it needs to be 30
                // digits as required by the h3 format
                model.tag.number += '0000000000';

                /** TODO: This should be moved in another module to make the link
                 *        between this one and :
                 *          - partner_contact_personal_information
                 *          - partner_contact_second_names
                 */
                // Send 00000000 isn't written to the medium so we have to write
                // an invalid birthdate for now
                var birthdate = '01010101';
                if (model.partner.birthdate_date !== false) {
                    birthdate = model.partner.birthdate_date.replace(/-/g, '');
                }

                // Store written data to be able to compare it with data returned
                // from the medium
                model.writtenData = {
                    birthdate: birthdate,
                    firstname: model.partner.firstname.toString().substring(0, 15),
                    lastname:  model.partner.lastname.toString().substring(0, 15),
                    user_id:   model.tag.number // eslint-disable-line
                };

                var method = 'write';
                var args = {
                    data: {
                        id:   model.transactionId,
                        data: model.writtenData
                    }
                };

                $.ajax($.extend({}, model.settings, {
                    url:  model.baseUrl + '/' + method,
                    data: JSON.stringify(args),
                })).done(controller.callback.ajaxSuccess).fail(controller.callback.ajaxError);
            });
        },
        enrollMedium: function () {
            model.enrollMedium('enroll');
        }
    };

    var view = {
        init: function ($dom, context) {
            view.context = context;
            view.$readMediumBtn = $dom.find('input[name="read-medium-btn"]');
            view.$formatMediumBtn = $dom.find('input[name="format-medium-btn"]');
            view.$writeMediumBtn = $dom.find('input[name="write-medium-btn"]');
            view.$enrollMediumBtn = $dom.find('input[name="enroll-medium-btn"]');

            view.$readSuccessDiv = $dom.find('div[name="read-success"]');
            view.$readWarningDiv = $dom.find('div[name="read-warning"]');
            view.$readErrorDiv = $dom.find('div[name="read-error"]');

            view.$readMediumBtn.val(_t('Read the medium'));
            view.$formatMediumBtn.val(_t('Format the medium'));
            view.$writeMediumBtn.val(_t('Write the medium'));
            view.$enrollMediumBtn.val(_t('Assign the medium'));


            view.$readMediumBtn.on('click', function () {
                view.resetDisplay();
                controller.readMedium();
            });

            view.$formatMediumBtn.on('click', function () {
                if (confirm(_t('Are you sure you want to format this medium?')) === true) {
                    view.resetDisplay();
                    controller.formatMedium(view.context);
                }
            });

            view.$writeMediumBtn.on('click', function () {
                if (confirm(_t('Are you sure you want to write on this medium?')) === true) {
                    view.resetDisplay();
                    controller.writeMedium(view.context);
                }
            });

            view.$enrollMediumBtn.on('click', function () {
                if (confirm(_t('Are you sure you want to assign this medium?')) === true) {
                    controller.enrollMedium();
                }
            });
        },

        resetDisplay: function () {
            framework.blockUI();
            view.$readSuccessDiv.addClass('hide');
            view.$readWarningDiv.addClass('hide');
            view.$readErrorDiv.addClass('hide');

            view.$readMediumBtn.removeAttr('disabled');
            view.$formatMediumBtn.attr('disabled', 'disabled');
            view.$writeMediumBtn.attr('disabled', 'disabled');
            view.$enrollMediumBtn.addClass('hide');
        },
        displayInformations: function (operation, data) {
            framework.unblockUI();
            switch (data.status) {
                case 'bad_format':
                    view.$readWarningDiv.removeClass('hide');
                    view.$readWarningDiv.text(_t("The medium isn't formatted to HLFAT."));
                    view.$formatMediumBtn.removeAttr('disabled');
                    break;
                case 'format_error':
                    view.$readErrorDiv.removeClass('hide');
                    view.$readErrorDiv.text(data.message);
                    view.$formatMediumBtn.removeAttr('disabled');
                    break;
                case 'format_ok':
                    view.$readSuccessDiv.removeClass('hide');
                    view.$readSuccessDiv.text(data.message);
                    view.$writeMediumBtn.removeAttr('disabled');
                    break;
                case 'empty_card':
                    view.$readWarningDiv.removeClass('hide');
                    view.$readWarningDiv.text(_t('The medium is empty.'));
                    view.$writeMediumBtn.removeAttr('disabled');
                    break;
                case 'no_reader':
                    view.$readWarningDiv.removeClass('hide');
                    view.$readWarningDiv.text(_t('No PCSC reader detected.'));
                    break;
                case 'no_card':
                    view.$readWarningDiv.removeClass('hide');
                    view.$readWarningDiv.text(_t('No medium detected.'));
                    break;
                case 'error':
                    view.$readErrorDiv.removeClass('hide');
                    view.$readErrorDiv.text(data.message);
                    // Never prevent the user to be able to write or format the medium
                    // as we don't handle correctly errors returned by windows service..
                    view.$formatMediumBtn.removeAttr('disabled');
                    view.$writeMediumBtn.removeAttr('disabled');
                    break;
                default:
                    view.$readSuccessDiv.removeClass('hide');
                    var message = _t('The medium contains the following informations:<br />') +
                        '<ul>' +
                        '<li>' + _t('birthdate') + ': ' + data.data.birthdate + '</li>' +
                        '<li>' + _t('firstname') + ': ' + data.data.firstname + '</li>' +
                        '<li>' + _t('lastname') + ': ' + data.data.lastname + '</li>' +
                        '<li>Tag ID: ' + data.data.user_id + '</li>' +
                        '<li>CSN: ' + data.data.serial_number + '</li>' +
                        '</ul>';

                    model.dataRead = data.data;

                    if (operation === 'read') {
                        if (!model.dataRead.user_id) {
                            view.$readSuccessDiv.addClass('hide');
                            view.$readWarningDiv.removeClass('hide');
                            view.$readWarningDiv.text(_t('The medium is empty.'));
                            view.$writeMediumBtn.removeAttr('disabled');
                            return;
                        }
                        model.isTagAssigned(model.dataRead.serial_number).then(function (assignations) {
                            if (assignations.length > 0) {
                                var record = assignations[0].reference_id.split(',')[0];
                                var partnerId = parseInt(assignations[0].reference_id.split(',')[1]);
                                if (partnerId !== view.context.default_reference_id && record === 'res.partner') {
                                    message += '<br />' +
                                        _t('This medium already belongs to another partner.') +
                                        '<br/>' +
                                        _t('You have to deactivate the medium first to be able to write on it.') +
                                        '<br/><br/>' +
                                        "<a href='/web#id=" + partnerId + "&view_type=form&model=res.partner'>" +
                                        _t('Click here to deactive the medium.') +
                                        '</a>';
                                } else {
                                    // We allow user to format or write on the partner's medium
                                    // as it appears this it's his own medium.
                                    view.$formatMediumBtn.removeAttr('disabled');
                                    view.$writeMediumBtn.removeAttr('disabled');
                                }
                            } else {
                                // In case there is no assignation for read tags e.g:
                                //  - unknown tags
                                //  - known tags but unassigned
                                // We allow user to enroll the medium or format it.
                                view.$enrollMediumBtn.removeClass('hide');
                                view.$formatMediumBtn.removeAttr('disabled');
                            }

                            view.$readSuccessDiv.html(message);
                        });
                    } else if (operation === 'write') {
                        model.enrollMedium(operation);
                        view.$readSuccessDiv.html(message);
                    }
            }
        },
        enrollmentSuccess: function () {
            framework.unblockUI();
            view.$readSuccessDiv.removeClass('hide');
            view.$readSuccessDiv.html(_t('The medium has successfully been assigned.'));
            view.$enrollMediumBtn.addClass('hide');
        }
    };

    var model = {
        // AJAX SETTINGS
        baseUrl:       '',
        transactionId: null,
        settings:      {
            method:      'POST',
            contentType: 'application/json',
            dataType:    'json',
            crossDomain: true,
            async:       true,
            timeout:     10000,
        },
        partnerObj:   'res.partner',
        wizardObj:    'partner.contact.identification.wizard.create.medium',
        writtenData:  {},
        dataRead:     {},
        // METHODS
        createMedium: function (data) {
            var params = {
                model: model.wizardObj,
                method: 'get_or_create_tag',
                args: [ 'csn', data.serial_number ]
            }
            $.when(
                model.call_method(params)
            ).done(function (tags) {
                $.when(
                    model.call_method({
                        model: model.wizardObj,
                        method: 'create_assignation',
                        args: [ model.tag.id, 'res.partner', model.partner.id]
                    }),
                    model.call_method({
                        model: model.wizardObj,
                        method: 'create_assignation',
                        args: [ tags[0].id, 'res.partner', model.partner.id]
                    })
                ).done(function () {
                model.call_method({
                        model: model.wizardObj,
                        method: 'create_medium',
                        args: [[model.tag.id, tags[0].id]]
                });
            });
        })
        },
        isTagAssigned: function (tagNumber) {
            var params = {
                model: model.wizardObj,
                method: 'is_tag_assigned',
                args: [tagNumber]
            }
            return model.call_method(params);
        },
        deleteCreatedTag: function () {
            if (model.tag !== null) {
                var params = {
                    model: model.wizardObj,
                    method: 'delete_tag',
                    args: [[model.tag.id]]
                }
                model.call_method(params);
            }
        },
        enrollMedium: function (operation) {
            if (operation === 'write') {
                $.extend(model.writtenData, {
                    'serial_number': model.dataRead.serial_number
                });

                delete model.dataRead['serial_number'];
                model.dataRead['serial_number'] = model.writtenData.serial_number;

                if (JSON.stringify(model.dataRead) === JSON.stringify(model.writtenData)) {
                    model.createMedium(model.writtenData);
                } else {
                    model.deleteCreatedTag();
                }
            } else if (operation === 'enroll') {
                var tag = model.dataRead.user_id;
                tag = tag.slice(0, 20);
                $.when(
                    model.call_method({
                        model: model.partnerObj,
                        method: 'search_read',
                        domain: [['id', '=', model.context.default_reference_id ]]
                    }),
                    model.call_method({
                        model: model.wizardObj,
                        method: 'get_or_create_tag',
                        args: [ 'h3', tag ]
                    })
                ).done(function (partners, tags) {
                    model.partner = partners[0];
                    model.tag = tags[0];

                    $.when(model.createMedium(model.dataRead)).done(function () {
                        view.enrollmentSuccess();
                    });
                });
            }
        },
        init: function (context) {
            var param = {
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['partner_contact_identification.windows_service_port']
                    }
            $.when(model.call_method(param)).done(function (port) {
                model.baseUrl = 'https://127.0.0.1:' + port;
                model.transactionId = Math.floor(Math.random() * (1000000 - 0 + 1)) + 0;
                model.context = context;

            });
        },
        //  improved
        call_method: function (param) {
            var args = param.args || [];
            var kwargs = param.kwargs || {};
            var domain = param.domain || [];
            if (!_.isArray(args)) {
                // call(method, kwargs)
                kwargs = args;
                args = [];
            }
            return rpc.query({
                model: param.model,
                method: param.method,
                args: args,
                kwargs: kwargs,
                domain: domain,
            })
        },
    };

    FormRenderer.include({
        _renderView: function () {
                var self = this
                return this._super.apply(this, arguments).then(function(){
                        if (self.$el.find('input[name="read-medium-btn"]').length) {
                            model.init(self.state.context);
                            view.init(self.$el, self.state.context);
                    }

                });
            },
        });

});
