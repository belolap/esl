#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import esl.table


def new(table=None):
    list_ = []
    if table is not None:
        assert isinstance(table, esl.table.Table), \
                                'table must be esl.table.Table'
        for k in table:
            list_.append(table[k])
    return list_


def append(list_, value):
    assert isinstance(list_, list), 'list must be pythons\' list'
    list_.append(value)


__extension__ = {
    'python_list': {
        'new': new,
        'append': append,
    }
}
