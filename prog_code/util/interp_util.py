"""Logic for interpreting user provided values.

Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

@author: Sam Pottinger
@license: GNU GPL v3
"""
from calendar import monthrange
from datetime import datetime, timedelta, date

DAYS_PER_MONTH = 30.42


def interpret_date(target_val):
    parts = list(map(lambda x: int(x), target_val.split('/')))
    return date(parts[0], parts[1], parts[2])


def monthdelta(d1, d2):
    if d1 >= d2:
        return 0

    return float((d2 - d1).days) / DAYS_PER_MONTH


def safe_int_interpret(target):
    """Interpret a value as an integer.

    @param target: The value to interpret.
    @return: Integer parsed or None if could not be parsed.
    @rtype: int or None
    """
    if target == None:
        return None

    try:
        return int(target)
    except ValueError:
        return None

def safe_float_interpret(target):
    """Interpret a value as an floating point value.

    @param target: The value to interpet.
    @return: Float parsed or None if could not be parsed.
    @rtype: float or None
    """
    if target == None:
        return None

    try:
        return float(target)
    except ValueError:
        return None

def operator_to_str(operator):
    """Convert a operator abreviation to a code description of it.

    @param operator: The abreviation to convert (ex. "eq")
    @type operator: str
    @return: The code description of operator (ex. "==")
    @rtype: str
    """
    if operator == 'eq':
        return '=='
    elif operator == 'lt':
        return '<'
    elif operator == 'gt':
        return '>'
    elif operator == 'neq':
        return '!='
    elif operator == 'lteq':
        return '<='
    elif operator == 'gteq':
        return '>='
    else:
        return '?'

def filter_to_str(target):
    """Convert a filter to a SQL clause.

    @param target: The filter to convert.
    @type target: models.Filter
    @return: The SQL clause ready string representation of the given filter.
    @rtype: str
    """
    operator_str = operator_to_str(target.operator)
    return '%s %s %s' % (target.field, operator_str, target.operand)
