from odoo import fields
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def convert_date_to_closing_datetime(closing_date):
    """Transforme une date/datetime en closing datetime (object, pas string).

    Exemples :
    - '2018-31-12'                  --> datetime(2019/01/01 00:00:00) +1
    - '2018-31-12 15:00:00'         --> datetime(2018/31/12 15:00:00)
    - date(2018/31/12)              --> datetime(2019/01/01 00:00:00) +1
    - datetime(2018/31/12 12:00)    --> datetime(2018/31/12 12:00:00)
    - '2019-01-01 00:00:00'         --> datetime(2019/01/01 00:00:00)
    - datetime(2018/31/12 00:00)    --> datetime(2018/31/12 00:00:00)
    """
    if not closing_date:
        return None
    if not isinstance(closing_date, (str, datetime, date)):
        raise ValueError('Expected date/datetime object or str (odoo date) got %s' % type(closing_date))
    result = closing_date

    if isinstance(closing_date, str):
        result = fields.Datetime.from_string(closing_date)
        # Si string (date ORM) alors vérifier si il existe une composante horaire
        if not len(closing_date) > fields.DATE_LENGTH:
            # Odoo add 00:00:00 has default time value
            result += relativedelta(days=+1)

    elif not result.time():
        # Si date, alors prendre le lendemain minuit
        result += relativedelta(days=+1)
        result = datetime(result.year, result.month, result.day)

    return result


def convert_closing_datetime_to_date(closing_date):
    """Transforme une date/datetime en closing datetime (object, pas string).

    Exemples :
    - '2018-31-12'                  --> date(2018/31/12)
    - '2017-31-12 15:00:00'         --> date(2017/31/12)
    - date(2018/31/12)              --> date(2018/31/12)
    - datetime(2018/31/12 12:00)    --> date(2018/31/12)
    - '2019-01-01 00:00:00'         --> date(2018/31/12) -1
    - datetime(2018/31/12 00:00)    --> date(2018/30/12) -1
    """
    if not closing_date:
        return None
    if not isinstance(closing_date, (str, datetime, date)):
        raise ValueError('Expected date/datetime object or str (odoo date) got %s' % type(closing_date))
    result = closing_date

    if isinstance(closing_date, str):
        # Si string (date ORM) alors vérifier si il existe une composante horaire
        result = fields.Datetime.from_string(closing_date)
        if len(closing_date) > fields.DATE_LENGTH and not result.time():
            # Si datetime ORM sans composante horaire, retrancher un jour
            result += relativedelta(days=-1)
        result = result.date()

    elif isinstance(result, datetime):
        # Si datetime, sans composante horaire, retrancher un jour
        result += relativedelta(days=-1)
        result = result.date()

    return result
