"""Tests for utility functions used in generating CSV downloads.

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

import mox

import report_util


class TestMCDIFormat:

    def __init__(self, details):
        self.details = details


class ReportUtilTest(mox.MoxTestBase):

    def test_sort_by_study_order(self):
        test_rows = [[0]]* 20 + [['word1'], ['word3'], ['word2'], ['word4']]
        test_format = TestMCDIFormat(
            {'categories': [
                {'words': ['word1', 'word2']},
                {'words': ['word3', 'word4']}
            ]}
        )
        sorted_rows = report_util.sort_by_study_order(test_rows, test_format)
        self.assertEqual(sorted_rows[20][0], 'word1')
        self.assertEqual(sorted_rows[21][0], 'word2')
        self.assertEqual(sorted_rows[22][0], 'word3')
        self.assertEqual(sorted_rows[23][0], 'word4')
