#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

from . import basic
from . import math
from . import table
from . import python_datetime
from . import python_decimal
from . import python_list

__extension__ = {}
__extension__.update(basic.__extension__)
__extension__.update(math.__extension__)
__extension__.update(table.__extension__)
__extension__.update(python_datetime.__extension__)
__extension__.update(python_decimal.__extension__)
__extension__.update(python_list.__extension__)
