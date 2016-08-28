__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

import collections


class Variables(collections.MutableMapping):

    def __init__(self, initial=None):
        self.__values = {'__builtins__': {}}
        if initial is not None:
            assert isinstance(initial, dict)
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


class Context(object):

    def __init__(self, globals_dict=None, locals_dict=None,
                 import_handler=None):
        self.__globals = Variables(globals_dict)
        self.__locals = Variables(locals_dict)

        self.import_handler = import_handler

        self.line_stack = []
        self.call_stack = []
        self.loops = []
        self.must_return = False

    def get(self, key):
        assert isinstance(key, str)
        if key in self.__locals:
            return self.__locals[key]
        elif key in self.__globals:
            return self.__globals[key]
        raise NameError('key `%s\' is not defined.' % key)

    def set(self, key, value):
        assert isinstance(key, str)
        self.__locals[key] = value

    def has_key(self, key):
        assert isinstance(key, str)
        if key in self.__locals:
            return True
        return key in self.__globals

    @property
    def globals(self):
        return dict(self.__globals)

    @property
    def locals(self):
        return self.__locals
