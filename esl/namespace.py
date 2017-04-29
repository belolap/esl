#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import collections


_DEFAULT = object()


class Variables(collections.MutableMapping):

    def __init__(self, initial=None):
        self.__values = {}
        if initial is not None:
            assert isinstance(initial, (dict, Variables))
            for k, v in initial.items():
                if not k.startswith('_'):
                    self.__values[k] = v

    def __getitem__(self, key):
        return self.__values[key]

    def __setitem__(self, key, value):
        if key.startswith('_'):
            raise KeyError('key mustn\'t starts with _')
        self.__values[key] = value

    def __delitem__(self, key):
        del self.__values[key]

    def __iter__(self):
        for key in self.__values:
            yield key

    def __len__(self):
        return len(self.__values)


class Namespace(object):

    def __init__(self, globals_dict=None, locals_dict=None,
                 import_handler=None):
        if globals_dict is None:
            globals_dict = {'__builtins__': {}}
        assert isinstance(globals_dict, dict)
        self.__globals = globals_dict
        self.__locals = Variables(locals_dict)

    def has_local(self, key):
        return key in self.__locals

    def has_global(self, key):
        return key in self.__globals

    def get(self, key, default=_DEFAULT):
        assert isinstance(key, str)
        if key in self.__locals:
            return self.__locals[key]
        elif key in self.__globals:
            return self.__globals[key]

        if default == _DEFAULT:
            raise NameError('key `%s\' is not defined.' % key)
        return default

    def set_global(self, key, value):
        assert isinstance(key, str)
        self.__globals[key] = value

    def set_local(self, key, value):
        assert isinstance(key, str)
        self.__locals[key] = value

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
        obj[key] = val

    def clone(self):
        ctx = Namespace(globals_dict=self.__globals)
        for k, v in self.__locals.items():
            ctx.set_local(k, v)
        return ctx

    @property
    def globals(self):
        return self.__globals

    @property
    def locals(self):
        return self.__locals
