"""Tests for utility functions used in managing API keys.

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
import unittest.mock

import prog_code.util.api_key_util as api_key_util
import prog_code.util.db_util as db_util
import prog_code.util.injection_util as injection_util
import prog_code.util.user_util as user_util


class APIKeyUtilTests(unittest.TestCase):

    def test_interp_csv_field(self):
        result = api_key_util.interp_csv_field('')
        self.assertEqual(result, [])

        result = api_key_util.interp_csv_field('test')
        self.assertEqual(result, ['test'])

        result = api_key_util.interp_csv_field('test,test2')
        self.assertEqual(result, ['test', 'test2'])

        result = api_key_util.interp_csv_field('test,test2,')
        self.assertEqual(result, ['test', 'test2', ''])

    def test_get_if_avail(self):
        result = api_key_util.get_if_avail(['1', '2', '3'], 2)
        self.assertEqual(result, '3')

        result = api_key_util.get_if_avail(['1', '2'], 2, 'DEFAULT')
        self.assertEqual(result, 'DEFAULT')

    def test_generate_new_api_key(self):
        with unittest.mock.patch('prog_code.util.db_util.get_api_key') as mock:
            mock.side_effect = [None, True, True, None]

            api_key_util.generate_new_api_key()
            api_key_util.generate_new_api_key()

            self.assertEqual(len(mock.mock_calls), 4)


    def test_create_new_api_key(self):
        with unittest.mock.patch('prog_code.util.api_key_util.db_util') as mock:
            mock.get_api_key = unittest.mock.MagicMock(side_effect=[True, None])
            mock.delete_api_key = unittest.mock.MagicMock()
            mock.create_new_api_key = unittest.mock.MagicMock()

            api_key_util.create_new_api_key('123')

            self.assertEqual(len(mock.get_api_key.mock_calls), 2)
            mock.delete_api_key.assert_called_with('123')
            self.assertEqual(len(mock.create_new_api_key.mock_calls), 1)
            self.assertEqual(mock.create_new_api_key.call_args[0][0], '123')
