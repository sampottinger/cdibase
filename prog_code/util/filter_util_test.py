"""Tests used for utility functions in applying database filters.

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

from ..struct import models

import prog_code.util.db_util as db_util
import prog_code.util.filter_util as filter_util


class TestDBCursor:

    def __init__(self):
        self.result = []
        self.queries = []
        self.operands = []

    def execute(self, query, operands):
        self.queries.append(query)
        self.operands.append(operands)

    def fetchall(self):
        return self.result


class TestDBConnection:

    def __init__(self, next_cursor):
        self.next_cursor = next_cursor
        self.closed = False

    def cursor(self):
        return self.next_cursor

    def close(self):
        self.close = True

    def commit(self):
        pass


class FilterUtilTests(unittest.TestCase):

    def test_run_search_query(self):
        fake_cursor = TestDBCursor()
        fake_connection = TestDBConnection(fake_cursor)

        self.mox.StubOutWithMock(db_util, 'get_db_connection')
        db_util.get_db_connection().AndReturn(fake_connection)
        self.mox.ReplayAll()

        filters = [
            models.Filter('study', 'eq', 'study1,study2')
        ]
        filter_util.run_search_query(filters, 'test')

        query = fake_cursor.queries[0]
        query_str ='SELECT * FROM test WHERE (study == ? OR study == ?) AND '\
            '(deleted == ?)'
        self.assertEqual(query, query_str)

        operands = fake_cursor.operands[0]
        self.assertEqual(len(operands), 3)
        self.assertEqual(operands[0], 'study1')
        self.assertEqual(operands[1], 'study2')
        self.assertEqual(operands[2], 0)

    def test_delete_search_query(self):
        fake_cursor = TestDBCursor()
        fake_connection = TestDBConnection(fake_cursor)

        self.mox.StubOutWithMock(db_util, 'get_db_connection')
        db_util.get_db_connection().AndReturn(fake_connection)
        self.mox.ReplayAll()

        filters = [
            models.Filter('study', 'eq', 'study1,study2')
        ]
        filter_util.run_delete_query(filters, 'test', True)

        query = fake_cursor.queries[0]
        query_str ='UPDATE test SET deleted=0 WHERE (study == ? OR study == ?)'
        self.assertEqual(query, query_str)

        operands = fake_cursor.operands[0]
        self.assertEqual(len(operands), 2)
        self.assertEqual(operands[0], 'study1')
        self.assertEqual(operands[1], 'study2')
