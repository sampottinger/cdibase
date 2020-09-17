"""Tests for utility functions used in managing file uploads.

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
import re
import unittest
import unittest.mock

import prog_code.util.file_util as file_util


class FileUtilTests(unittest.TestCase):

    def test_generate_filename(self):
        filename = file_util.generate_filename(
            '.csv',
            length=3,
            chars=['a', 'b', 'c']
        )
        self.assertEqual(len(filename), 7)

        chars_regex = re.compile('[abc]{3}\.csv')
        self.assertIsNotNone(chars_regex.match(filename))

    def test_generate_unique_filename(self):
        with unittest.mock.patch('prog_code.util.file_util.upload_exists') as mock:
            mock.side_effect = [True, True, False]

            filename = file_util.generate_unique_filename('.csv')
            self.assertIn('.csv', filename)

            self.assertEqual(len(mock.mock_calls), 3)

    def test_allowed_file(self):
        self.assertTrue(file_util.allowed_file('test.csv'))
        self.assertFalse(file_util.allowed_file('test.exe'))
        self.assertFalse(file_util.allowed_file('test'))
