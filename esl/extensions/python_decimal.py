__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

import decimal


def new(val):
    return decimal.Decimal(val)


__extension__ = {
    'python_decimal': {
        'new': new,
    }
}
