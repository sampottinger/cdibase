import copy

import mox

from ..struct import models

import constants
import db_util
import recalc_util


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
        ]
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


class RecalcPercentilesTest(mox.MoxTestBase):

    def test_load_mcdi_model(self):
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        db_util.load_mcdi_model('test_format').AndReturn(TEST_MCDI_MODEL)
        self.mox.ReplayAll()

        adapter = recalc_util.CachedMCDIAdapter()
        result_1 = adapter.load_mcdi_model('test_format')
        result_2 = adapter.load_mcdi_model('test_format')

        self.assertEqual(result_1, TEST_MCDI_MODEL)
        self.assertEqual(result_2, TEST_MCDI_MODEL)

    def test_load_percentile_model(self):
        self.mox.StubOutWithMock(db_util, 'load_percentile_model')
        db_util.load_percentile_model('test_format').AndReturn(TEST_MCDI_MODEL)
        self.mox.ReplayAll()

        adapter = recalc_util.CachedMCDIAdapter()
        result_1 = adapter.load_percentile_model('test_format')
        result_2 = adapter.load_percentile_model('test_format')

        self.assertEqual(result_1, TEST_MCDI_MODEL)
        self.assertEqual(result_2, TEST_MCDI_MODEL)

    def test_get_max_mcdi_words(self):
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        db_util.load_mcdi_model('test_format').AndReturn(TEST_MCDI_MODEL)
        self.mox.ReplayAll()

        adapter = recalc_util.CachedMCDIAdapter()
        result_1 = adapter.get_max_mcdi_words('test_format')
        result_2 = adapter.get_max_mcdi_words('test_format')

        self.assertEqual(result_1, 5)
        self.assertEqual(result_2, 5)

    def test_recalculate_age(self):
        test_snapshot = copy.deepcopy(TEST_SNAPSHOT)
        recalc_util.recalculate_age(test_snapshot)
        self.assertTrue(abs(test_snapshot.age - 17.71) < 0.01)

    def test_recalculate_percentile(self):
        adapter = recalc_util.CachedMCDIAdapter()
        adapter.max_word_counts['standard'] = 681
        adapter.mcdi_models['standard'] = TEST_MCDI_MODEL
        adapter.percentiles['typical-male'] = TEST_PERCENTILES_MODEL
        test_snapshot = copy.deepcopy(TEST_SNAPSHOT)

        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.ReplayAll()

        recalc_util.recalculate_age(test_snapshot)
        recalc_util.recalculate_percentile(test_snapshot, adapter)
        self.assertTrue(abs(test_snapshot.age - 17.71) < 0.01)
