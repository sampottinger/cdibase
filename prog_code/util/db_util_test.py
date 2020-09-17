"""Tests for database utility functions.

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
import copy
import re
import unittest

from ..struct import models

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util

TEST_SNAPSHOT_ID = 789
TEST_DB_ID = 123
TEST_STUDY_ID = 456
TEST_STUDY = 'test study'
TEST_BIRTHDAY = '2011/09/12'
TEST_ITEMS_EXCLUDED = 3
TEST_EXTRA_CATEGORIES = 4
TEST_NUM_LANGUAGES = 2
TEST_HARD_OF_HEARING = constants.EXPLICIT_FALSE

TEST_SNAPSHOT = models.SnapshotMetadata(
    TEST_SNAPSHOT_ID,
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    24,
    TEST_BIRTHDAY,
    '2013/10/12',
    20,
    25,
    100,
    TEST_ITEMS_EXCLUDED,
    50,
    TEST_EXTRA_CATEGORIES,
    0,
    ['english','spanish'],
    TEST_NUM_LANGUAGES,
    'standard',
    TEST_HARD_OF_HEARING,
    False
)


class FakeCursor:

    def __init__(self):
        self.commands = []
        self.committed = False
        self.closed = False
        self.lastrowid = 1

    def execute(self, command, params):
        self.commands.append((command, params))
        self.committed = False

    def commit(self):
        self.committed = True

    def close(self):
        self.close = True


class FakeConnection:

    def __init__(self, cursor):
        self.cursor = cursor


class DBUtilTests(unittest.TestCase):

    def test_clean_up_date(self):
        self.assertEqual(db_util.clean_up_date('1992/1/10'), '1992/01/10')
        self.assertEqual(db_util.clean_up_date('1992/01/10'), '1992/01/10')

    def test_update_snapshot(self):
        fake_cursor = FakeCursor()

        db_util.update_snapshot(TEST_SNAPSHOT, fake_cursor)

        self.assertEqual(len(fake_cursor.commands), 1)

        test_command = fake_cursor.commands[0]
        self.assertTrue('child_id=?,' in test_command[0])
        self.assertEqual(TEST_SNAPSHOT.child_id, test_command[1][0])
        self.assertEqual(TEST_SNAPSHOT.languages, test_command[1][14].split(','))

    def test_update_snapshot_new_id(self):
        fake_cursor = FakeCursor()

        snapshot = copy.copy(TEST_SNAPSHOT)
        snapshot.child_id = None
        db_util.update_snapshot(snapshot, fake_cursor)

        self.assertEqual(len(fake_cursor.commands), 2)

        test_command = fake_cursor.commands[1]
        self.assertTrue('child_id=?,' in test_command[0])
        self.assertNotEqual(TEST_SNAPSHOT.child_id, test_command[1][1])
        self.assertEqual(TEST_SNAPSHOT.languages, test_command[1][14].split(','))

    def test_update_participant_metadata_all(self):
        fake_cursor = FakeCursor()

        db_util.update_participant_metadata(
            TEST_SNAPSHOT.child_id,
            TEST_SNAPSHOT.gender,
            TEST_SNAPSHOT.birthday,
            TEST_SNAPSHOT.hard_of_hearing,
            TEST_SNAPSHOT.languages,
            cursor=fake_cursor
        )

        self.assertEqual(len(fake_cursor.commands), 1)

        test_command = fake_cursor.commands[0]
        self.assertTrue('child_id=?' in test_command[0])
        self.assertEqual(TEST_SNAPSHOT.gender, test_command[1][0])
        self.assertEqual(TEST_SNAPSHOT.birthday, test_command[1][1])
        self.assertEqual(TEST_SNAPSHOT.hard_of_hearing, test_command[1][2])
        self.assertEqual(TEST_SNAPSHOT.languages, test_command[1][3].split(','))
        self.assertEqual(TEST_SNAPSHOT.child_id, test_command[1][4])

    def test_update_participant_metadata_select(self):
        fake_cursor = FakeCursor()

        db_util.update_participant_metadata(
            TEST_SNAPSHOT.child_id,
            TEST_SNAPSHOT.gender,
            TEST_SNAPSHOT.birthday,
            TEST_SNAPSHOT.hard_of_hearing,
            TEST_SNAPSHOT.languages,
            cursor=fake_cursor,
            snapshot_ids=[
                {'study': 'test-study-1', 'id': 1},
                {'study': 'test-study-1', 'id': 2}
            ]
        )

        self.assertEqual(len(fake_cursor.commands), 2)

        test_command = fake_cursor.commands[0]
        self.assertEqual(TEST_SNAPSHOT.gender, test_command[1][0])
        self.assertEqual(TEST_SNAPSHOT.birthday, test_command[1][1])
        self.assertEqual(TEST_SNAPSHOT.hard_of_hearing, test_command[1][2])
        self.assertEqual(TEST_SNAPSHOT.languages, test_command[1][3].split(','))
        self.assertEqual(TEST_SNAPSHOT.child_id, test_command[1][4])
        self.assertEqual('test-study-1', test_command[1][5])
        self.assertEqual(1, test_command[1][6])

        test_command = fake_cursor.commands[1]
        self.assertEqual('test-study-1', test_command[1][5])
        self.assertEqual(2, test_command[1][6])
