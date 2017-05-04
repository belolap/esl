#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import collections


_DEFAULT = object()


class Namespace(object):

    def __init__(self, globals_dict=None, locals_dict=None,
                 import_handler=None):
        if globals_dict is None:
            globals_dict = {'__builtins__': {}}
        assert isinstance(globals_dict, dict)
        self.__globals = globals_dict

        if locals_dict is None:
            locals_dict = {}
        assert isinstance(locals_dict, dict)
        self.__locals = locals_dict

    # Get dicts for function call
    @property
    def globals(self):
        return self.__globals

    @property
    def locals(self):
        return self.__locals

    # Globals and locals manipulation
    def set_global(self, key, value):
        assert isinstance(key, str)
        self.__globals[key] = value

    def set_local(self, key, value):
        assert isinstance(key, str)
        self.__locals[key] = value

    def del_global(self, key):
        assert isinstance(key, str)
        del self.__globals[key]

    def del_local(self, key):
        assert isinstance(key, str)
        del self.__locals[key]

    def get_global(self, key, default=_DEFAULT):
        try:
            return self.__globals[key]
        except KeyError:
            if default == _DEFAULT:
                raise
            return default

    def get_local(self, key, default=_DEFAULT):
        try:
            return self.__locals[key]
        except KeyError:
            if default == _DEFAULT:
                raise
            return default

    def has_global(self, key):
        return key in self.__globals

    def has_local(self, key):
        return key in self.__locals

    # Object's attributes manipulation
    def check_key(self, obj, key):
        assert isinstance(key, str)
        if key.startswith('_'):
            raise KeyError('access denied')

    def get_attribute(self, obj, key, default=_DEFAULT):
        self.check_key(obj, key)
        try:
            value = getattr(obj, key)
        except AttributeError:
            if default == _DEFAULT:
                raise
            else:
                value = default
        return value

    def set_attribute(self, obj, key, value):
        self.check_key(obj, key)
        setattr(obj, key, value)

    def del_attribute(self, obj, key):
        self.check_key(obj, key)
        delattr(obj, key)

    def get_item(self, obj, key, default=_DEFAULT):
        self.check_key(obj, key)
        try:
            value = obj[key]
        except KeyError:
            if default == _DEFAULT:
                raise
            else:
                value = default
        return value

    def set_item(self, obj, key, value):
        self.check_key(obj, key)
        obj[key] = value

    def del_item(self, obj, key):
        self.check_key(obj, key)
        del obj[key]

    # New namespace
    def clone(self):
        ns = Namespace(globals_dict=self.__globals)
        for k, v in self.__locals.items():
            ns.set_local(k, v)
        return ns
