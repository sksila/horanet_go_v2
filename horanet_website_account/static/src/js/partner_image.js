odoo.define('horanet_website_account.PartnerImage', function (require) {
    var Class = require('web.Class');

    var PartnerImage = Class.extend({
        init: function ($selector) {
            var self = this;
            this._initSelector($selector);

            var $uploadCrop;

            this.$inputAvatar.change(function () {
                if (this.files && this.files[0]) {
                    // On cache l'avatar
                    self.$imgAvatar.hide();
                    // On initialise le croppie qu'une seule fois
                    if (typeof $uploadCrop === "undefined") {
                        $uploadCrop = $('#croppie-div').croppie({
                            customClass: 'center-block',
                            showZoomer: false,
                            viewport: {
                                width: 170,
                                height: 220,
                                type: 'square',
                            },
                            boundary: {
                                width: 180,
                                height: 230,
                            },
                        });
                    }
                    // On montre le croppie avec son bouton et on cache le bouton d'upload
                    $uploadCrop.show();
                    $('.file-upload').hide();
                    $('.btn-croppie').show();

                    var reader = new FileReader();
                    reader.onload = function (upload) {
                        $uploadCrop.croppie('bind', {
                            url: upload.target.result,
                        });
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
            $('.btn-croppie').on('click', function () {
                $uploadCrop.croppie('result', {
                    type: 'canvas',
                    size: 'viewport',
                }).then(function (resp) {
                    // On remplace l'avatar par l'image du croppie
                    self.$imgAvatar.attr('src', resp);
                    self.$base64Avatar.val(resp);
                    // on cache le croppie avec son bouton, on affiche l'avatar avec son bouton d'upload
                    $uploadCrop.hide();
                    $('.btn-croppie').hide();
                    self.$imgAvatar.show();
                    $('.file-upload').show();
                });
            });
        },
        _initSelector: function ($selector) {
            this.$base64Avatar = $selector.find("input[name='image_base64']");
            this.$inputAvatar = $selector.find("input[type='file'][name=input_avatar]");
            this.$imgAvatar = $selector.find('img[name=img_avatar]');
        },
    });

    return PartnerImage;
});
