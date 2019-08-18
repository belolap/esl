__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from typing import Any, Dict

from . import basic
from . import math
from . import table
from . import python_datetime
from . import python_timedelta
from . import python_decimal
from . import python_list

__extension__: Dict[str, Any] = {}
__extension__.update(basic.__extension__)
__extension__.update(math.__extension__)
__extension__.update(table.__extension__)
__extension__.update(python_datetime.__extension__)
__extension__.update(python_timedelta.__extension__)
__extension__.update(python_decimal.__extension__)
__extension__.update(python_list.__extension__)
