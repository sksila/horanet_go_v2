odoo.define('horanet_website_account.PartnerPhone', function () {
    var PartnerPhone = function ($countryPhone, $countryPhoneCode, $countryMobile, $countryMobileCode) {
        // Déclaration des variables


        // On change le code d'appel du pays si on change de pays
        $countryPhone.change(function () {
            $countryPhoneCode.val([ 'country_phone', '=', parseInt($countryPhone.val()) ]);
        });

        $countryMobile.change(function () {
            $countryMobileCode.val([ 'country_mobile', '=', parseInt($countryMobile.val()) ]);
        });
    };
    return PartnerPhone;
});