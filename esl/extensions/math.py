__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'


def round_(val):
    return round(val)


__extension__ = {
    'math': {
        'round': round_,
    }
}
