"""Tests for recalculating prior values in the database.

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
import unittest
import unittest.mock

from ..struct import models

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util
import prog_code.util.recalc_util as recalc_util


TEST_SNAPSHOT_ID = 789
TEST_DB_ID = 123
TEST_STUDY_ID = 456
TEST_STUDY = 'test study'
TEST_BIRTHDAY = '2012/05/09'
TEST_ITEMS_EXCLUDED = 3
TEST_EXTRA_CATEGORIES = 4
TEST_NUM_LANGUAGES = 2
TEST_HARD_OF_HEARING = constants.EXPLICIT_FALSE

TEST_MCDI_MODEL = models.MCDIFormat(
    'human_name',
    'safe_name',
    'filename',
    {
        'percentiles': {
            'male': 'typical-male'
        },
        'categories': [
            {
                'words': ['word1', 'word2']
            },
            {
                'words': ['word3', 'word4', 'word5']
            }
        ],
        'count_as_spoken': [1, 2]
    }
)

TEST_PERCENTILES_MODEL = models.PercentileTable(
    'human_name',
    'safe_name',
    'filename',
    [
        [25,4,6,7,10,13,16,21,26,33,40,47,55,62,69,75],
        [20,4,5,6,8,11,14,18,22,28,34,41,48,56,63,69],
        [15,3,4,0,7,9,12,15,18,23,29,35,41,48,55,62],
        [10,3,3,4,5,7,9,11,14,18,22,27,32,38,45,51]
    ]
)

TEST_SNAPSHOT = models.SnapshotMetadata(
    TEST_SNAPSHOT_ID,
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    24,
    TEST_BIRTHDAY,
    '2013/10/30',
    20,
    -1,
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


class RecalcPercentilesTest(unittest.TestCase):

    def test_load_mcdi_model(self):
        with unittest.mock.patch('prog_code.util.db_util.load_mcdi_model') as mock:
            mock.return_value = TEST_MCDI_MODEL

            adapter = recalc_util.CachedMCDIAdapter()
            result_1 = adapter.load_mcdi_model('test_format')
            result_2 = adapter.load_mcdi_model('test_format')

            self.assertEqual(result_1, TEST_MCDI_MODEL)
            self.assertEqual(result_2, TEST_MCDI_MODEL)

            mock.assert_called_with('test_format')

    def test_load_percentile_model(self):
        with unittest.mock.patch('prog_code.util.db_util.load_percentile_model') as mock:
            mock.return_value = TEST_MCDI_MODEL

            adapter = recalc_util.CachedMCDIAdapter()
            result_1 = adapter.load_percentile_model('test_format')
            result_2 = adapter.load_percentile_model('test_format')

            self.assertEqual(result_1, TEST_MCDI_MODEL)
            self.assertEqual(result_2, TEST_MCDI_MODEL)

            mock.assert_called_with('test_format')

    def test_get_max_mcdi_words(self):
        with unittest.mock.patch('prog_code.util.db_util.load_mcdi_model') as mock:
            mock.return_value = TEST_MCDI_MODEL

            adapter = recalc_util.CachedMCDIAdapter()
            result_1 = adapter.get_max_mcdi_words('test_format')
            result_2 = adapter.get_max_mcdi_words('test_format')

            self.assertEqual(result_1, 5)
            self.assertEqual(result_2, 5)

            mock.assert_called_with('test_format')

    def test_recalculate_age(self):
        test_snapshot = copy.deepcopy(TEST_SNAPSHOT)
        recalc_util.recalculate_age(test_snapshot)
        self.assertTrue(abs(test_snapshot.age - 17.71) < 0.01)

    def test_recalculate_percentile(self):
        with unittest.mock.patch('prog_code.util.db_util.load_mcdi_model') as mock_mcdi:
            with unittest.mock.patch('prog_code.util.db_util.load_snapshot_contents') as mock_snap:
                adapter = recalc_util.CachedMCDIAdapter()
                adapter.max_word_counts['standard'] = 681
                adapter.mcdi_models['standard'] = TEST_MCDI_MODEL
                adapter.percentiles['typical-male'] = TEST_PERCENTILES_MODEL
                test_snapshot = copy.deepcopy(TEST_SNAPSHOT)

                test_word_1 = models.SnapshotContent(0, '', 1, 0)
                test_word_2 = models.SnapshotContent(0, '', 2, 0)
                test_word_3 = models.SnapshotContent(0, '', 3, 0)
                words_spoken = [test_word_1] * 31
                words_spoken.extend([test_word_2] * 22)
                words_spoken.extend([test_word_3] * 13)
                mock_snap.return_value = words_spoken

                recalc_util.recalculate_age(test_snapshot)
                recalc_util.recalculate_percentile(test_snapshot, adapter)
                self.assertTrue(abs(test_snapshot.age - 17.71) < 0.01)
                self.assertEqual(test_snapshot.words_spoken, 53)
                self.assertEqual(test_snapshot.percentile, 14)

                mock_snap.assert_called_with(test_snapshot)
                self.assertEqual(len(mock_mcdi.mock_calls), 0)
