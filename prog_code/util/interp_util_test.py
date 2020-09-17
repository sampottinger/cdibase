"""Tessts for utility functions used in interpreting user-provided values.

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
"""
import datetime
import unittest

from ..struct import models

import prog_code.util.interp_util as interp_util


class InterpUtilTests(unittest.TestCase):

    def test_interpret_date(self):
        expected_date = datetime.date(2010, 3, 20)
        generated_date = interp_util.interpret_date('2010/03/20')
        self.assertEqual(expected_date, generated_date)

    def test_monthdelta(self):
        d1 = datetime.date(2010, 3, 20)
        d2 = datetime.date(2012, 3, 10)
        d3 = datetime.date(2015, 3, 10)

        self.assertTrue(abs(interp_util.monthdelta(d1, d2) - 23.7) < 0.01)
        self.assertTrue(abs(interp_util.monthdelta(d1, d3) - 59.7) < 0.01)
        self.assertEqual(interp_util.monthdelta(d1, d1), 0)
        self.assertEqual(interp_util.monthdelta(d2, d1), 0)

    def test_monthdelta_invalid_time(self):
        d1 = datetime.date(2010, 3, 20)
        d2 = datetime.date(2012, 3, 10)

        self.assertEqual(interp_util.monthdelta(d1, d1), 0)
        self.assertEqual(interp_util.monthdelta(d2, d1), 0)

    def test_safe_int_interpret(self):
        self.assertEqual(interp_util.safe_int_interpret(None), None)
        self.assertEqual(interp_util.safe_int_interpret('test'), None)
        self.assertEqual(interp_util.safe_int_interpret('123'), 123)
        self.assertEqual(interp_util.safe_int_interpret('123.4'), None)

    def test_safe_float_interpret(self):
        self.assertEqual(interp_util.safe_float_interpret(None), None)
        self.assertEqual(interp_util.safe_float_interpret('test'), None)
        self.assertEqual(interp_util.safe_float_interpret('123'), 123)
        self.assertEqual(interp_util.safe_float_interpret('123.4'), 123.4)

    def test_operator_to_str(self):
        self.assertEqual(interp_util.operator_to_str('lteq'), '<=')
        self.assertEqual(interp_util.operator_to_str('unknown'), '?')

    def test_filter_to_str(self):
        test_filter = models.Filter('operand', 'gteq', 'operator')
        test_str = interp_util.filter_to_str(test_filter)
        self.assertEqual(test_str, 'operand >= operator')
