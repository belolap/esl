__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

import esl.table
import esl.interpreter


def next_(obj, key=None):
    if isinstance(obj, list):
        keys = range(0, len(obj))
    elif isinstance(obj, dict):
        keys = list(sorted(obj.keys()))
    elif isinstance(obj, esl.table.Table):
        keys = [x for x in obj]

    length = len(obj)

    if isinstance(obj, esl.table.Table):
        if key is None:
            key = 0

        if isinstance(key, int):
            if key < length:
                key += 1
                return key, obj[key]
            elif key == length:
                key = None

        if key is None:
            index = length
        else:
            index = keys.index(key) + 1

    elif isinstance(obj, list):
        if key is None:
            key = 0
        else:
            key += 1

        if key >= length:
            return None

        index = key

    elif isinstance(obj, dict):
        if key is None:
            index = 0
        else:
            index = keys.index(key) + 1

    if (index >= len(keys)):
        return None

    key = keys[index]

    return key, obj[key]


def pairs(obj):
    return next_, obj, None


async def ipairs(obj):
    if hasattr(obj, '__aiter__'):
        func = await obj.__aiter__()
    elif hasattr(obj, '__iter__'):
        func = obj(iter)
    return func, obj, 0


def error(message, level=None):
    # level is not used
    raise esl.interpreter.ESLRuntimeError(message)


def assert_(expression, message):
    if not expression:
        error(message)


__extension__ = {
    'next': next_,
    'pairs': pairs,
    'ipairs': ipairs,
    'error': error,
    'assert': assert_,
}
