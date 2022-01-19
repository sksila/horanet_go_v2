from odoo import _
import re


def validation_phone_number(data, country_phone_code, national_prefix, error, error_message):
    """
    Check phone number.

    Phone number format accepted:
    1- Phone number without national prefix
    2- Phone number with the correct national prefix
    3- Phone number with the correct country phone code and without national prefix
    4- Phone number with the correct country phone code, the sign '+' and without national prefix

    :param data: the data of the field phone
    :param country_phone_code: the country phone code of the chosen phone country
    :param national_prefix: the national prefix of the chosen phone country
    :param error: error dictionary
    :param error_message: list of error messages

    """
    if data:
        phone = data.replace(' ', '').replace('-', '').replace('.', '').replace('/', '')

        if country_phone_code == 33:    # France
            pattern = "^(?:\+33|0|33)\s*[1-9](?:[\s.-]*\d{2}){4}$|^[1-9]{1}(?:[\s.-]*\d{2}){4}$"
            if not re.match(pattern, phone):
                error['phone'] = 'error'
                error_message.append(_("Enter a valid phone number."))

        elif phone.isnumeric() or (phone[0] == '+' and phone[1:].isnumeric()):
            length = len(str(country_phone_code))
            if phone[0] == "+" and len(phone[1:]) <= 15:
                if phone[1:length + 1] != str(country_phone_code) or \
                        (national_prefix and phone[length + 1:length + 1 + len(national_prefix)] == national_prefix):
                    error['phone'] = 'error'
                    error_message.append(_("Enter a valid phone number."))
            elif phone[0:length] == str(country_phone_code) and len(phone) <= 15:
                if national_prefix and phone[length:length + len(national_prefix)] == national_prefix:
                    error['phone'] = 'error'
                    error_message.append(_("Enter a valid phone number."))
            elif len(phone) > 15-length:
                error['phone'] = 'error'
                error_message.append(_("Enter a valid phone number."))
        else:
            error['phone'] = 'error'
            error_message.append(_("Enter a valid phone number."))

    return error, error_message


def validation_mobile_number(data, country_mobile_code, mobile_prefix, error, error_message):
    """
    Check mobile number.

    mobile number format accepted:
    1- Mobile number with a correct mobile prefix (with or without 0 at the first place)
    2- Mobile number with the correct country phone code and a correct mobile prefix
    3- Mobile number with the correct country phone code, the sign '+' and a correct mobile prefix

    :param data: the data of the field mobile
    :param country_mobile_code: the country phone code of the chosen mobile country
    :param mobile_prefix: list of the mobile prefix(separated by ',') of the chosen mobile country
    :param error: error dictionary
    :param error_message: list of error messages

    """
    if data:
        mobile = data.replace(" ", "").replace("-", "").replace(".", "").replace("/", "")
        if mobile_prefix and country_mobile_code == 33:   # France
            error_france = True
            for prefix in mobile_prefix.split(','):
                pattern = "^(?:\+33|0|33)\s*"+prefix+"(?:[\s.-]*\d{2}){4}$|^"+prefix+"{1}(?:[\s.-]*\d{2}){4}$"
                if re.match(pattern, mobile):
                    error_france = False
            if error_france:
                error['mobile'] = 'error'
                error_message.append(_("Enter a valid mobile number."))

        elif (mobile.isnumeric() or (mobile[0] == "+" and mobile[1:].isnumeric())) and\
                (len(mobile) + len(str(country_mobile_code))) <= 16:
            length = len(str(country_mobile_code))

            if mobile_prefix and mobile[0] == "+" and len(mobile[1:]) <= 15:
                if mobile[1:1 + length] != str(country_mobile_code) or \
                        (mobile_prefix and mobile[1 + length:1 + length + 1] not in mobile_prefix.split(',')):
                    error['mobile'] = 'error'
                    error_message.append(_("Enter a valid mobile number."))

            elif mobile_prefix and mobile[0:length] == str(country_mobile_code) and len(mobile) <= 15:
                if mobile_prefix and mobile[length:length + 1] not in mobile_prefix.split(','):
                    error['mobile'] = 'error'
                    error_message.append(_("Enter a valid mobile number."))

            elif mobile_prefix and mobile[0] == '0' and mobile[1] not in mobile_prefix.split(',') and\
                    len(mobile) <= 16-length:
                error['mobile'] = 'error'
                error_message.append(_("Enter a valid mobile number."))

            elif mobile_prefix and mobile[0] not in mobile_prefix.split(',') and mobile[0] != '0' and\
                    len(mobile) <= 15-length:
                error['mobile'] = 'error'
                error_message.append(_("Enter a valid mobile number."))

            elif len(mobile) > 15-length:
                error['mobile'] = 'error'
                error_message.append(_("Enter a valid mobile number."))
        else:
            error['mobile'] = 'error'
            error_message.append(_("Enter a valid mobile number."))

    return error, error_message
