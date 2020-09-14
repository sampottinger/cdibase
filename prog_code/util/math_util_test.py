"""Tests of mathemtaical routines.

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
import unittest

import prog_code.util.math_util as math_util

TEST_PERCENTILE_TABLE = [
    [None,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
    [99,308,365,421,473,519,557,588,612,630,644,654,662,667,671,674],
    [95,156,204,259,319,380,439,492,537,574,603,625,641,652,661,667],
    [90,140,177,220,268,319,371,422,469,511,547,577,601,620,635,647],
    [85,127,1610,198,240,286,335,383,430,474,513,546,575,598,617,632],
    [80,11,141,175,215,259,306,355,403,448,490,527,558,584,606,623],
    [75,99,125,155,190,229,272,318,364,409,452,492,526,557,582,603],
    [70,91,114,141,172,208,248,390,334,378,421,462,499,531,560,584],
    [65,76,96,120,149,182,220,261,305,351,396,439,479,514,546,572],
    [60,63,81,103,129,161,197,237,281,327,374,419,462,501,535,564],
    [55,50,66,85,109,138,172,212,257,304,353,402,448,490,527,559],
    [50,43,57,74,95,121,152,189,230,276,324,372,420,464,504,539],
    [45,36,47,61,80,102,130,164,203,247,294,343,392,439,483,521],
    [40,31,41,53,70,90,116,146,183,224,270,319,368,417,462,503],
    [35,28,36,47,62,80,103,130,163,210,244,291,340,388,435,478],
    [30,23,30,39,51,67,86,111,140,174,214,259,306,355,403,449],
    [25,21,27,36,46,60,77,97,123,153,189,229,272,319,366,412],
    [20,19,24,31,39,50,63,80,101,125,154,187,224,265,308,353],
    [15,15,20,25,32,41,52,66,82,103,127,156,189,225,265,308],
    [10,12,15,20,25,32,40,51,64,79,99,121,148,179,213,251],
    [5,8,10,13,16,20,25,31,38,48,59,72,88,108,130,156]
]


class MathUtilTests(unittest.TestCase):

    def test_get_with_end_max(self):
        test_list = [1, 2, 3]
        result = math_util.get_with_end_max(test_list, 0)
        self.assertEqual(result, 1)
        result = math_util.get_with_end_max(test_list, 3)
        self.assertEqual(result, 3)

    def test_find_percentile(self):
        percentile = math_util.find_percentile(
            TEST_PERCENTILE_TABLE,
            0,
            30,
            667
        )
        self.assertTrue(percentile >= 0 and percentile <= 5)

        percentile = math_util.find_percentile(
            TEST_PERCENTILE_TABLE,
            155,
            30,
            667
        )
        self.assertTrue(percentile >= 0 and percentile <= 5)

        percentile = math_util.find_percentile(
            TEST_PERCENTILE_TABLE,
            537,
            24,
            667
        )
        self.assertTrue(percentile >= 90 and percentile <= 95)

        percentile = math_util.find_percentile(
            TEST_PERCENTILE_TABLE,
            574,
            24,
            667
        )
        self.assertTrue(percentile >= 95 and percentile <= 100)

        percentile = math_util.find_percentile(
            TEST_PERCENTILE_TABLE,
            630,
            24,
            667
        )
        self.assertTrue(percentile >= 99 and percentile <= 100)

        percentile = math_util.find_percentile(
            TEST_PERCENTILE_TABLE,
            667,
            24,
            667
        )
        self.assertTrue(percentile >= 99 and percentile <= 100)
