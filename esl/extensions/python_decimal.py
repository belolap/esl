#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import decimal


def new(val):
    return decimal.Decimal(val)


__extension__ = {
    'python_decimal': {
        'new': new,
    }
}
