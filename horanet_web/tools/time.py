import math


def float_time_to_str(time_float, default='00:00'):
    """Format time Float to str like 'hh:mn'.

    :param time_float: time in float (hours.minutes)
    :param default: if time_float is None, default value is returned.
    :return: time in a string.
    """
    if not time_float:
        return default

    factor = time_float < 0 and -1 or 1
    val = abs(time_float)
    hours, minutes = (factor * int(math.floor(val)), int(round((val % 1) * 60)))

    hours = str(hours)
    minutes = str(minutes)

    if len(hours) != 2:
        hours = '0' + hours
    if len(minutes) != 2:
        minutes = '0' + minutes

    return hours + ':' + minutes
