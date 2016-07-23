__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'


class Context(object):
    def __init__(self, globals_dict={}, locals_dict={}):
        self.__globals = dict(globals_dict)
        self.__locals = dict(locals_dict)
        self.line_stack = []
        self.call_stack = []
        self.loops = []
        self.must_return = False
        self.import_handler = None

    def get(self, key):
        if not isinstance(key, str):
            raise TypeError('параметр `key\' должен быть строкой, '
                            'а не типом `{}\''.format(type(key)))
        if key in self.__globals:
            return self.__globals[key]
        elif key in self.__locals:
            return self.__locals[key]
        raise NameError('key `%s\' is not defined.' % key)

    def set(self, key, value):
        if not isinstance(key, str):
            raise TypeError('параметр `key\' должен быть строкой, '
                            'а не типом `{}\''.format(type(key)))
        if key in self.__globals:
            self.__globals[key] = value
        elif key in self.__locals:
            self.__locals[key] = value
        else:
            raise NameError('key `%s\' is not defined.' % key)

    def getGlobals(self):
        return self.__globals

    def getLocals(self):
        return self.__locals

    def addGlobal(self, key, value):
        if not isinstance(key, str):
            raise TypeError('параметр `key\' должен быть строкой, '
                            'а не типом `{}\''.format(type(key)))
        if key in self.__globals:
            raise KeyError('globals already have key `%s\'.' % key)
        self.__globals[key] = value

    def addLocal(self, key, value):
        if not isinstance(key, str):
            raise TypeError('параметр `key\' должен быть строкой, '
                            'а не типом `{}\''.format(type(key)))
        if key in self.__locals:
            raise KeyError('locals already have key `%s\'.' % key)
        self.__locals[key] = value

    def has_key(self, key):
        if not isinstance(key, str):
            raise TypeError('параметр `key\' должен быть строкой, '
                            'а не типом `{}\''.format(type(key)))
        if key in self.__globals:
            return True
        return key in self.__locals

    def push_line(self, lineno):
        self.line_stack.append(lineno)

    def pop_line(self):
        del self.line_stack[-1]

    def setImportHandler(self, handler):
        self.import_handler = handler
