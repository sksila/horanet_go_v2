from validate_email import validate_email

from odoo import _, http
from odoo.http import request

try:
    from odoo.addons.auth_signup.controllers.main import AuthSignupHome
    from odoo.addons.auth_signup_verify_email.controllers.main import SignupVerifyEmail
except ImportError:
    from auth_signup.controllers.main import AuthSignupHome
    from auth_signup_verify_email.controllers.main import SignupVerifyEmail

import logging

_logger = logging.getLogger(__name__)


class HoranetSignUp(AuthSignupHome):
    """This class contains overrided methods of the AuthSignupHome class."""

    @http.route()  # route '/web/signup'
    def web_auth_signup(self, *args, **kw):
        u"""Surcharge de la fonction pour ajouter un paramètre d'enregistrement des pros."""
        signup = super(HoranetSignUp, self).web_auth_signup(*args, **kw)

        base_config = request.env['base.config.settings'].sudo()
        partner_titles = request.env['res.partner.title'].sudo().search([])

        partner_person_titles = None
        if base_config.get_auth_signup_allow_title_person():
            partner_person_titles = partner_titles.filtered(lambda t: not t.is_company_title)
        signup.qcontext['partner_person_titles'] = partner_person_titles

        partner_company_titles = None
        if base_config.get_auth_signup_allow_title_company():
            partner_company_titles = partner_titles.filtered('is_company_title')
        signup.qcontext['partner_company_titles'] = partner_company_titles

        signup.qcontext['post'] = kw
        return signup

    def _signup_with_values(self, token, values, *args, **kwargs):
        u"""Surcharge de _signup_with_values.

        - Corriger un problème de gestion de langue (web browser et norme ISO)
        """
        # Vérification de la langue
        user_lang = values.get('lang', False)
        # Get the first language to match by case insensitive comparison
        if user_lang:
            matching_lang = request.env['res.lang'].search([('code', '=ilike', user_lang.lower())])
            if matching_lang:
                values['lang'] = matching_lang[0].code
            else:
                values.pop('lang')

        return super(HoranetSignUp, self)._signup_with_values(token, values, *args, **kwargs)


class OtherHoranetSignup(SignupVerifyEmail):
    """To override passwordless_signup."""

    # On surcharge cette méthode pour avoir un message d'erreur plus explicite en cas d'email déjà existant
    def passwordless_signup(self, values):
        """Signup without password and overrided to have more explicit error messages."""
        qcontext = self.get_auth_signup_qcontext()

        # Check good format of e-mail
        if not validate_email(values.get("login", "")):
            qcontext["error"] = _("That does not seem to be an email address.")
            return request.render("auth_signup.signup", qcontext)
        elif not values.get("email"):
            values["email"] = values.get("login")

        # Check email confirmation
        if values.get('login', '').lower() != qcontext.get('confirm_login', '').lower():
            qcontext["error"] = _("Email do not match, please retype them.")
            return request.render("auth_signup.signup", qcontext)

        is_company = bool(values.get('is_company', 'True') == 'True')
        values['is_company'] = is_company
        if is_company:
            values['firstname'] = ''
            values['lastname'] = values['name']
            values.pop('select_person_title', '')
            if 'select_company_title' in values:
                select_company_title_id = values.pop('select_company_title')
                if select_company_title_id.isdigit():
                    values['title'] = int(select_company_title_id)
                else:
                    qcontext["error"] = _("Please select a company title.")
                    return request.render("auth_signup.signup", qcontext)
            if 'select_company_title' in values:
                values['title'] = int(values.pop('select_company_title'))
        else:
            values['name'] = values.get('firstname', '') + ' ' + values.get('lastname', '')
            values.pop('select_company_title', '')
            if 'select_person_title' in values:
                select_person_title_id = values.pop('select_person_title')
                if select_person_title_id.isdigit():
                    values['title'] = int(select_person_title_id)

        # Remove password
        values["password"] = ''
        sudo_users = (request.env["res.users"].with_context(create_user=True).sudo())

        try:
            # Remove unused value to avoid log warning
            values.pop('confirm_login')
            values.pop('redirect')
            values.pop('token')
            sudo_users.signup(values, qcontext.get("token"))
            sudo_users.reset_password(values.get("login"))
            # On met le partner en inactif
            user = sudo_users.search([('login', '=', values.get("login"))])
            user.partner_id.write({'active': False})
        except Exception as error:
            # Duplicate key or wrong SMTP settings, probably
            _logger.exception(error)
            request.env.cr.rollback()

            if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                qcontext["error"] = _("Another user is already registered using this email address.")
            else:
                # Agnostic message for security
                qcontext["error"] = _("Something went wrong, please try again later or contact us.")

            return request.render("auth_signup.signup", qcontext)

        qcontext["message"] = _("Check your email to activate your account!")
        return request.render("auth_signup.reset_password", qcontext)
