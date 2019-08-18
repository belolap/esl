__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'


class Function(object):
    def __init__(self, parlist, body):
        self.parlist = parlist
        self.body = body
        self.self = None
