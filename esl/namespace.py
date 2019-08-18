__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from esl.table import Table

logger = getLogger(__name__)

_DEFAULT = object()


class Namespace(object):
    def __init__(self, local_vars=None, parent=None, import_handler=None):
        if local_vars is None:
            local_vars = {}
        self.__vars = local_vars
        self.__parent = parent

    # Variables manipulation
    def set_var(self, key, value, local=False):
        assert isinstance(key, str)
        if key in self.__vars or local or not self.__parent:
            self.__vars[key] = value
        else:
            self.__parent.set_var(key, value)

    def get_var(self, key):
        assert isinstance(key, str)
        if key in self.__vars:
            return self.__vars[key]
        if self.__parent is not None:
            return self.__parent.get_var(key)

    def del_var(self, key):
        assert isinstance(key, str)
        if key in self.__vars:
            del self.__vars[key]
        elif self.__parent:
            self.__parent.del_var(key)

    # Object's attributes manipulation
    def check_key(self, obj, key):
        assert isinstance(key, (str, int))
        if isinstance(key, str) and key.startswith('_'):
            raise KeyError('access denied')

    def set_attribute(self, obj, key, value):
        self.check_key(obj, key)
        setattr(obj, key, value)

    def del_attribute(self, obj, key):
        self.check_key(obj, key)
        delattr(obj, key)

    def has_attribute(self, obj, key):
        return hasattr(obj, key)

    def get_attribute(self, obj, key):
        self.check_key(obj, key)
        return getattr(obj, key, None)

    def set_item(self, obj, key, value):
        self.check_key(obj, key)
        obj[key] = value

    def del_item(self, obj, key):
        self.check_key(obj, key)
        del obj[key]

    def get_item(self, obj, key):
        self.check_key(obj, key)
        if isinstance(obj, dict):
            return obj.get(key)
        elif isinstance(obj, Table):
            return obj[key]
        raise TypeError('unsupported type.')

    def has_item(self, obj, key):
        return key in obj

    # New namespace
    def clone(self):
        return Namespace(parent=self)
