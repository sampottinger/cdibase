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

import mox

import api_key_util
import user_util
import db_util


class APIKeyUtilTests(mox.MoxTestBase):

    def test_interp_csv_field(self):
        result = api_key_util.interp_csv_field('')
        self.assertEqual(result, [])

        result = api_key_util.interp_csv_field('test')
        self.assertEqual(result, ['test'])

        result = api_key_util.interp_csv_field('test,test2')
        self.assertEqual(result, ['test', 'test2'])

        result = api_key_util.interp_csv_field('test,test2,')
        self.assertEqual(result, ['test', 'test2', ''])

    def test_get_list_item_if_avail(self):
        result = api_key_util.get_list_item_if_avail(['1', '2', '3'], 2)
        self.assertEqual(result, '3')

        result = api_key_util.get_list_item_if_avail(['1', '2'], 2, 'DEFAULT')
        self.assertEqual(result, 'DEFAULT')

    def test_generate_new_api_key(self):
        self.mox.StubOutWithMock(db_util, 'read_api_key_model_record')

        db_util.read_api_key_model_record(mox.IsA(basestring)).AndReturn(None)
        db_util.read_api_key_model_record(mox.IsA(basestring)).AndReturn(True)
        db_util.read_api_key_model_record(mox.IsA(basestring)).AndReturn(True)
        db_util.read_api_key_model_record(mox.IsA(basestring)).AndReturn(None)

        self.mox.ReplayAll()

        api_key_util.generate_new_api_key()
        api_key_util.generate_new_api_key()


    def test_create_api_key_model(self):
        self.mox.StubOutWithMock(db_util, 'read_api_key_model_record')
        self.mox.StubOutWithMock(db_util, 'delete_api_key_model')
        self.mox.StubOutWithMock(db_util, 'create_api_key_model')

        db_util.read_api_key_model_record('123').AndReturn(True)
        db_util.delete_api_key_model('123')
        db_util.read_api_key_model_record(mox.IsA(basestring)).AndReturn(None)
        db_util.create_api_key_model('123', mox.IsA(basestring))

        self.mox.ReplayAll()

        api_key_util.create_api_key_model('123')
