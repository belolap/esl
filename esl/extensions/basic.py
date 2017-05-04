#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import esl


def next(table, key=None):
    assert isinstance(table, esl.Table)
    length = len(table)
    if key is None:
        key = 0
    if isinstance(key, int):
        if key < length:
            key += 1
            return key, table[key]
        elif key == length:
            key = None

    keys = [x for x in table]
    if key is None:
        index = length
    else:
        index = keys.index(key) + 1
    if (index >= len(keys)):
        return None
    key = keys[index]
    return key, table[key]


def pairs(table):
    return next, table, None


def error(message, level=None):
    # level is not used
    raise esl.ESLRuntimeError(message)


def assert_(expression, message):
    if not expression:
        error(message)
