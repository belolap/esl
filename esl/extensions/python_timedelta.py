#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'


import datetime


def new(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    return datetime.timedelta(days, seconds, microseconds, milliseconds, minutes, hours, weeks)


__extension__ = {
    'python_timedelta': {
        'new': new,
    }
}

