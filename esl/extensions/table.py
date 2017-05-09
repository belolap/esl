#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'


def insert(table, value):
    table[len(table)+1] = value


__extension__ = {
    'table': {
        'insert': insert,
    }
}
