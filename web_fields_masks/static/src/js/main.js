odoo.define('web_fields_masks.Masks', function (require) {
    'use strict';

    // On importe la classe InputField
    var InputField = require('web.basic_fields').InputField;

    InputField.include({
        mask: '',
        init: function () {
            this._super.apply(this, arguments);
            if (_.has(this.attrs, 'data-inputmask')) {
                this.mask = this.attrs['data-inputmask'];
            }
        },
        // On surcharge la fonction RenderElement pour ajouter le masque
        renderElement: function () {
            var self = this;
            this._super.apply(this, arguments);
            // Si l'élément est un input (uniquement en mode édition) et qu'il a un mask
            if (this.mask !== '' && this.$el && this.mode === 'edit') {
                this.$el.attr('data-inputmask', this.mask);
                this.$el.inputmask(undefined, {
                    onincomplete: function () {
                        self.$el.addClass('oe_form_editable');
                    },
                    oncomplete: function () {
                        self.$el.removeClass('oe_form_editable');
                    }
                });
            }
        }
    });

});
