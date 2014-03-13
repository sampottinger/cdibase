import re

import mox

from ..struct import models

import constants
import db_util

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
    'english,spanish',
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


class DBUtilTests(mox.MoxTestBase):
    
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
        self.assertEqual(TEST_SNAPSHOT.languages, test_command[1][14])
