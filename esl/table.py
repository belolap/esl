#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import collections


class Table(object):

    def __init__(self):
        self.__numbered = []
        self.__named = collections.OrderedDict()

    def __getitem__(self, key):
        if isinstance(key, float):
            if key.is_integer():
                key = int(key)
        if isinstance(key, int):
            if key > 0 and key <= len(self.__numbered):
                return self.__numbered[key-1]
        return self.__named.get(key)

    def __setitem__(self, key, value):
        if isinstance(key, float):
            if key.is_integer():
                key = int(key)
        if isinstance(key, int):
            if key > 0 and key < len(self.__numbered):
                if value is None:
                    del self.__numbered[key-1]
                else:
                    self.__numbered[key-1] = value
                return
            elif (key - 1) == len(self.__numbered):
                if value is None:
                    del self.__numbered[key-1]
                else:
                    self.__numbered.append(value)
                    key += 1
                    while key in self.__named:
                        self.__numbered.append(self.__named.pop(key))
                        key += 1
                return
        if not isinstance(key, (int, str, float)):
            raise TypeError('incorrect key type')
        self.__named[key] = value

    def __delitem__(self, key):
        if isinstance(key, float):
            if key.is_integer():
                key = int(key)
        try:
            del self.__numbered[key-1]
        except IndexError:
            pass

        try:
            del self.__named[key]
        except KeyError:
            pass

    def __iter__(self):
        for i in range(0, len(self.__numbered)):
            yield i + 1
        for k, v in self.__named.items():
            yield k

    def __len__(self):
        return len(self.__numbered)
