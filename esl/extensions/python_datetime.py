__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

import datetime


def strftime(date, frmt):
    if isinstance(date, datetime.datetime):
        return date.strftime(frmt)


__extension__ = {
    'python_datetime': {
        'strftime': strftime,
    }
}
