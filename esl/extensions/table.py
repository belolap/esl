__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'


def insert(table, value):
    table[len(table) + 1] = value


__extension__ = {
    'table': {
        'insert': insert,
    }
}
