#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

from .table import Table
from .function import Function
from .namespace import Namespace
from .interpreter import Interpreter, ESLSyntaxError, ESLRuntimeError
