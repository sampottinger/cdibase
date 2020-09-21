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
import datetime
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

    def __init__(self, results=None):
        self.commands = []
        self.committed = False
        self.closed = False
        self.lastrowid = 1
        self.result_i = 0
        self.results = results if results != None else []

    def execute(self, command, params=None):
        self.commands.append((command, params))
        self.committed = False

    def commit(self):
        self.committed = True

    def close(self):
        self.close = True

    def fetchone(self):
        if self.result_i >= len(self.results):
            return None
        else:
            val = self.results[self.result_i]
            self.result_i += 1
            return val

    def fetchall(self):
        return self.results


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

    def test_get_consent_settings_no_prior(self):
        fake_cursor = FakeCursor()

        result = db_util.get_consent_settings('test', fake_cursor)

        self.assertEqual(result.study, 'test')
        self.assertEqual(result.requirement_type, constants.CONSENT_FORM_NONE)
        self.assertEqual(result.form_content, '')
        self.assertEqual(result.other_options, [])
        self.assertEqual(result.updated, None)

    def test_get_consent_settings_prior(self):
        fake_cursor = FakeCursor([
            (
                'test',
                constants.CONSENT_FORM_ONCE,
                'form content',
                'option 1\noption, 2',
                1600705368
            )
        ])

        result = db_util.get_consent_settings('test', fake_cursor)

        expected_update = datetime.datetime.utcfromtimestamp(1600705368)

        self.assertEqual(result.study, 'test')
        self.assertEqual(result.requirement_type, constants.CONSENT_FORM_ONCE)
        self.assertEqual(result.form_content, 'form content')
        self.assertEqual(result.other_options, ['option 1', 'option, 2'])
        self.assertEqual(result.updated, expected_update)

    def test_put_consent_settings(self):
        fake_cursor = FakeCursor()
        new_settings = models.ConsentFormSettings(
            'test',
            constants.CONSENT_FORM_ALWAYS,
            'test content',
            ['option, 1', 'option 2'],
            datetime.datetime(2020, 1, 30, 2, 3, 4)
        )

        db_util.put_consent_settings(new_settings, fake_cursor)

        self.assertEqual(len(fake_cursor.commands), 1)
        self.assertTrue('INSERT' in fake_cursor.commands[0][0])
        test_command = fake_cursor.commands[0][1]
        self.assertEqual(test_command[0], 'test')
        self.assertEqual(test_command[1], constants.CONSENT_FORM_ALWAYS)
        self.assertEqual(test_command[2], 'test content')
        self.assertEqual(test_command[3], 'option, 1\noption 2')
        self.assertNotEqual(
            test_command[4],
            int(datetime.datetime(2020, 1, 30, 2, 3, 4).timestamp())
        )

    def test_get_consent_filings(self):
        fake_cursor = FakeCursor([
            (
                'study',
                'parent 1',
                '123',
                1600705368,
                'option 1',
                'parent1@example.com',
                'key_1'
            ),
            (
                'study',
                'parent 2',
                '124',
                1600705369,
                'option 2\noption 3',
                'parent2@example.com',
                'key_2'
            )
        ])

        results = db_util.get_consent_filings('study', fake_cursor)

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].study, 'study')
        self.assertEqual(results[0].name, 'parent 1')
        self.assertEqual(results[0].child_id, '123')
        self.assertEqual(results[0].other_options, ['option 1'])
        self.assertEqual(results[0].email, 'parent1@example.com')
        self.assertEqual(results[0].access_key, 'key_1')
        self.assertEqual(
            results[0].completed,
            datetime.datetime.utcfromtimestamp(1600705368)
        )

        self.assertEqual(results[1].study, 'study')
        self.assertEqual(results[1].name, 'parent 2')
        self.assertEqual(results[1].child_id, '124')
        self.assertEqual(results[1].other_options, ['option 2', 'option 3'])
        self.assertEqual(results[1].email, 'parent2@example.com')
        self.assertEqual(results[1].access_key, 'key_2')
        self.assertEqual(
            results[1].completed,
            datetime.datetime.utcfromtimestamp(1600705369)
        )

    def test_put_consent_filing(self):
        fake_cursor = FakeCursor()

        filing = models.ConsentFormFiling(
            'study',
            'parent 2',
            '124',
            datetime.datetime(2020, 1, 30, 2, 3, 4),
            ['option 2', 'option 3'],
            'parent2@example.com',
            'test_key_2'
        )

        db_util.put_consent_filing(filing, fake_cursor)

        self.assertEqual(len(fake_cursor.commands), 1)
        self.assertTrue('INSERT' in fake_cursor.commands[0][0])
        test_command = fake_cursor.commands[0][1]
        self.assertEqual(test_command[0], 'study')
        self.assertEqual(test_command[1], 'parent 2')
        self.assertEqual(test_command[2], '124')
        self.assertEqual(
            test_command[3],
            int(datetime.datetime(2020, 1, 30, 2, 3, 4).timestamp())
        )
        self.assertEqual(test_command[4], 'option 2\noption 3')
        self.assertEqual(test_command[5], 'parent2@example.com')
        self.assertEqual(test_command[6], 'test_key_2')

    def test_delete_consent_filings(self):
        fake_cursor = FakeCursor()
        db_util.delete_consent_filings('test@example.com', fake_cursor)
        self.assertEqual(len(fake_cursor.commands), 1)
        self.assertTrue('DELETE' in fake_cursor.commands[0][0])
        self.assertTrue('test@example.com' in fake_cursor.commands[0][1])
