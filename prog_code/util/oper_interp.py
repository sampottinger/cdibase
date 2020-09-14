"""Strategies for interpreting user input as filter operand values.

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

import prog_code.util.constants as constants


class FieldInfo(object):
    """Abstract base class for interpreters that produce filter operands.

    Abstract base class for strategies that interpret user input to produce
    values suitable for use in building models.Filter instances and, ultimately,
    SQL SELECT queries.
    """

    def __init__(self, field_name):
        """Create a new user input interpreter for the given field.

        @param field_name: The name of snapshot metadata field to filter on.
        @type field_name: str
        """
        self.__field_name = field_name

    def get_field_name(self):
        """Get the name of the snapshot metadata field that this filters on.

        @return: Database name for the column this value interpreter parses
            operand values for.
        @rtype: str
        """
        return self.__field_name

    def interpret_value(self, val):
        if isinstance(val, basestring):
            return val.split(',')
        else:
            return [val]


class DateInterpretField(FieldInfo):
    """A value interpreter for filter operands that returns original input.

    User input interpreter for filter operand values that returns original user
    input without interpretation.
    """

    def __init__(self, field_name):
        super(DateInterpretField, self).__init__(field_name)

    def interpret_single(self, val):
        parts = val.split('/')
        return parts[2] + '/' + parts[0] + '/' + parts[1]

    def interpret_value(self, val):
        """Return user provided operand value without interpretation.

        @param val: The original user provided operand value.
        @type val: str
        @return: Originally provided value.
        @rtype: str
        """
        vals = FieldInfo.interpret_value(self, val)
        vals = map(lambda x: self.interpret_single(x), vals)
        return vals


class RawInterpretField(FieldInfo):
    """A value interpreter for filter operands with date info."""

    def __init__(self, field_name):
        super(RawInterpretField, self).__init__(field_name)

    def interpret_value(self, val):
        """Return user provided operand interpreted as a date.

        @param val: The original user provided operand value.
        @type val: str
        @return: Date transformed string.
        @rtype: str
        """
        vals = FieldInfo.interpret_value(self, val)
        return vals


class GenderField(FieldInfo):
    """A value interpreter for gender based filter operands.

    User input interpreter for filter operand values that converts various
    string descriptions of gender to its numerical equivalent."""

    MALE_VALUES = ['male', 'boy', 'man']
    FEMALE_VALUES = ['female', 'girl', 'lady', 'woman']
    OTHER_VALUES = ['other', 'transgender', 'trans', 'intersex']

    def __init__(self, field_name):
        super(GenderField, self).__init__(field_name)

    def interpret_value(self, val):
        """Return user provided operand value interpreted as a gender.

        @param val: The original user provided operand value.
        @type val: str
        @return: Gender constant from util.constants or original value if it
            could not be interepreted.
        @rtype: int
        """
        vals = FieldInfo.interpret_value(self, val)

        ret_vals = []
        for val in vals:
            if not isinstance(val, basestring):
                ret_vals.append(val)
            else:
                val = val.lower()
                if val in self.MALE_VALUES:
                    ret_vals.append(constants.MALE)
                elif val in self.FEMALE_VALUES:
                    ret_vals.append(constants.FEMALE)
                elif val in self.OTHER_VALUES:
                    ret_vals.append(constants.OTHER_GENDER)
                else:
                    self.append(val)

        return ret_vals


class BooleanField(FieldInfo):
    """A value interpreter for boolean filter operands.

    User input interpreter for filter operand values that converts string
    representations of boolean values to actual boolean values.
    """

    TRUE_VALUES = ['true', 'yes', 'y', 't', 'on']
    FALSE_VALUES = ['false', 'no', 'n', 'f', 'off']

    def __init__(self, field_name):
        super(BooleanField, self).__init__(field_name)

    def interpret_value(self, val):
        """Return user provided operand value interpreted as a boolean value.

        @param val: The original user provided operand value.
        @type val: str
        @return: Cooresponding boolean value or originally provided value if it
            could not be interpreted.
        @rtype: bool
        """
        vals = FieldInfo.interpret_value(self, val)

        ret_vals = []
        for val in vals:
            if not isinstance(val, str):
                ret_vals.append(val)
            else:
                val = val.lower()
                if val in self.TRUE_VALUES:
                    ret_vals.append(True)
                elif val in self.FALSE_VALUES:
                    ret_vals.append(False)
                else:
                    ret_vals.append(val)

        return ret_vals


class NumericalField(FieldInfo):
    """A value interpreter for numerical filter operands.

    User input interpreter for filter operand values that converts string
    representations of numerical values to actual numerical values.
    """

    def __init__(self, field_name):
        super(NumericalField, self).__init__(field_name)

    def interpret_value(self, val):
        """Return user provided operand value interpreted as a numerical value.

        @param val: The original user provided operand value.
        @type val: str
        @return: Cooresponding numerical value or originally provided value if
            it could not be interpreted.
        @rtype: float
        """
        vals = FieldInfo.interpret_value(self, val)

        ret_vals = []
        for val in vals:
            try:
                ret_vals.append(float(val))
            except ValueError:
                ret_vals.append(val)
        return ret_vals
