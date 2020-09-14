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
import unittest

from ..struct import models
from ..util import constants

import prog_code.util.db_util as db_util
import prog_code.util.report_util as report_util

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


class TestMCDIFormat:

    def __init__(self, details):
        self.details = details


class ReportUtilTest(unittest.TestCase):

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

    def test_summarize_snapshots(self):
        test_snap_1 = TEST_SNAPSHOT.clone()
        test_snap_1.mcdi_type = 'mcdi_type_1'
        test_snap_1.session_date = '2015/01/01'

        test_snap_2 = TEST_SNAPSHOT.clone()
        test_snap_2.mcdi_type = 'mcdi_type_1'
        test_snap_2.session_date = '2015/02/01'

        test_snap_3 = TEST_SNAPSHOT.clone()
        test_snap_3.mcdi_type = 'mcdi_type_2'
        test_snap_3.session_date = '2015/03/01'

        test_metadata = [test_snap_1, test_snap_2, test_snap_3]

        test_contents_1 = [
            models.SnapshotContent(0, 'word1', 1, 1),
            models.SnapshotContent(0, 'word2', 0, 1),
            models.SnapshotContent(0, 'word3', 0, 1)
        ]
        test_contents_2 = [
            models.SnapshotContent(0, 'word1', 1, 1),
            models.SnapshotContent(0, 'word2', 2, 1),
            models.SnapshotContent(0, 'word3', 0, 1)
        ]
        test_contents_3 = [
            models.SnapshotContent(0, 'word1', 1, 1),
            models.SnapshotContent(0, 'word2', 1, 1),
            models.SnapshotContent(0, 'word3', 1, 1),
            models.SnapshotContent(0, 'word4', 2, 1)
        ]

        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_snapshot_contents')

        db_util.load_mcdi_model('mcdi_type_1').AndReturn(
            models.MCDIFormat('', '', '', {'count_as_spoken': [1, 2]})
        )
        db_util.load_snapshot_contents(test_metadata[0]).AndReturn(
            test_contents_1
        )

        db_util.load_snapshot_contents(test_metadata[1]).AndReturn(
            test_contents_2
        )

        db_util.load_mcdi_model('mcdi_type_2').AndReturn(
            models.MCDIFormat('', '', '', {'count_as_spoken': [1]})
        )
        db_util.load_snapshot_contents(test_metadata[2]).AndReturn(
            test_contents_3
        )

        self.mox.ReplayAll()

        serialization = report_util.summarize_snapshots(test_metadata)

        self.assertEqual(serialization['word1'], '2015/01/01')
        self.assertEqual(serialization['word2'], '2015/02/01')
        self.assertEqual(serialization['word3'], '2015/03/01')
        self.assertEqual(serialization['word4'], None)
