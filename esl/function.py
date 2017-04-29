#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'


class Function(object):

    def __init__(self, parlist, body):
        self.parlist = parlist
        self.body = body
