"""Strategies for interpreting user input as filter operand values.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import constants


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


class RawInterpretField(FieldInfo):
    """A value interpreter for filter operands that returns original input.

    User input interpreter for filter operand values that returns original user
    input without interpretation.
    """

    def __init__(self, field_name):
        super(RawInterpretField, self).__init__(field_name)

    def interpret_value(self, val):
        """Return user provided operand value without interpretation.

        @param val: The original user provided operand value.
        @type val: str
        @return: Originally provided value.
        @rtype: str
        """
        return val


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
        if not isinstance(val, basestring):
            return val

        val = val.lower()
        if val in self.MALE_VALUES:
            return constants.MALE
        elif val in self.FEMALE_VALUES:
            return constants.FEMALE
        elif val in self.OTHER_VALUES:
            return constants.OTHER_GENDER
        else:
            return val


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
        if not isinstance(val, str):
            return val

        val = val.lower()
        if val in self.TRUE_VALUES:
            return True
        elif val in self.FALSE_VALUES:
            return False
        else:
            return val


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
        try:
            return float(val)
        except ValueError:
            return val
