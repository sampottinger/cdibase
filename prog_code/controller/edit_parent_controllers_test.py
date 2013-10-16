import collections
import copy
from datetime import date

import mox

import daxlabbase
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import math_util
from ..util import parent_account_util
from ..util import user_util
from ..struct import models

TEST_MCDI_TYPE = 'standard'
TEST_PARENT_FORM_ID = 20
TEST_CHILD_NAME = 'Test Child'
TEST_PARENT_EMAIL = 'parent@example.com'
TEST_EMAIL = 'test_mail'
TEST_DB_ID = 123
TEST_STUDY_ID = 456
TEST_SNAPSHOT_ID = 789
TEST_ITEMS_EXCLUDED = 3
TEST_EXTRA_CATEGORIES = 4
TEST_MOD_LANGUAGES = 'english'
TEST_MOD_NUM_LANGUAGES = 1
TEST_LANGUAGES = 'english.spanish'
TEST_NUM_LANGUAGES = 2
TEST_HARD_OF_HEARING = False
TEST_STUDY = 'test study'
TEST_BIRTHDAY = '2011/09/12'
TEST_BIRTHDAY_DATE = date(2011, 9, 12)
TEST_PARENT_FORM_ID_MOD = 30
TEST_CHILD_NAME_MOD = 'Test Child2'
TEST_PARENT_EMAIL_MOD = 'parent2@example.com'
TEST_DB_ID_MOD = 321
TEST_STUDY_ID_MOD = 654
TEST_STUDY_MOD = 'test study 2'
TEST_BIRTHDAY_MOD = '2011/09/13'
TEST_BIRTHDAY_DATE_MOD = date(2011, 9, 13)
TEST_ITEMS_EXCLUDED_MOD = 7
TEST_EXTRA_CATEGORIES_MOD = 8
TEST_NUM_LANGUAGES_MOD = 1
TEST_USER = models.User(
    TEST_DB_ID,
    TEST_EMAIL,
    None,
    False,
    True,
    False,
    False,
    True,
    False
)
TEST_API_KEY = 'abc123'
TEST_API_KEY_ENTRY = models.APIKey(
    TEST_EMAIL,
    TEST_API_KEY
)
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
    TEST_HARD_OF_HEARING
)
MALE_TEST_PERCENTILE_NAME = 'male_test_percentiles'
FEMALE_TEST_PERCENTILE_NAME = 'female_test_percentiles'
OTHER_TEST_PERCENTILE_NAME = 'other_test_percentiles'
TEST_FORMAT = models.MCDIFormat(
    'standard',
    'standard',
    'standard.yaml',
    {
        'categories': [
            {'words':['cat_1_word_1', 'cat_1_word_2', 'cat_1_word_3']},
            {'words':['cat_2_word_1', 'cat_2_word_2', 'cat_2_word_3']}
        ],
        'percentiles': {
            'male': MALE_TEST_PERCENTILE_NAME,
            'female': FEMALE_TEST_PERCENTILE_NAME,
            'other': OTHER_TEST_PERCENTILE_NAME
        },
        'options': [
            {'name': 'said', 'value': 1},
            {'name': 'not said', 'value': 0}
        ],
        'count_as_spoken': [1],
        'meta': {'mcdi_type': 'multilingual-test'}
    }
)
TEST_PRESENTATION_FORMAT_METADATA = models.PresentationFormat(
    'standard',
    'standard',
    'standard.yaml',
    {
        'male': 'male',
        'female': 'female',
        'explicit_other': 'other',
        'explicit_true': 'true',
        'explicit_false': 'false'
    }
)
EXPECTED_PARENT_FORM = models.ParentForm(
    TEST_PARENT_FORM_ID,
    TEST_CHILD_NAME,
    TEST_PARENT_EMAIL,
    'standard',
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    TEST_BIRTHDAY,
    TEST_ITEMS_EXCLUDED,
    TEST_EXTRA_CATEGORIES,
    'english,spanish',
    TEST_NUM_LANGUAGES,
    constants.EXPLICIT_FALSE
)
EXPECTED_MODIFIED_PARENT_FORM = models.ParentForm(
    TEST_PARENT_FORM_ID_MOD,
    TEST_CHILD_NAME_MOD,
    TEST_PARENT_EMAIL_MOD,
    'standard',
    TEST_DB_ID_MOD,
    TEST_STUDY_ID_MOD,
    TEST_STUDY_MOD,
    constants.FEMALE,
    TEST_BIRTHDAY_MOD,
    TEST_ITEMS_EXCLUDED_MOD,
    TEST_EXTRA_CATEGORIES_MOD,
    TEST_MOD_LANGUAGES,
    TEST_MOD_NUM_LANGUAGES,
    constants.EXPLICIT_TRUE
)
SEND_FORM_DATA_TEMPLATE = {
    'global_id': TEST_DB_ID,
    'study_id': TEST_STUDY_ID,
    'study': TEST_STUDY,
    'gender': constants.MALE,
    'birthday': TEST_BIRTHDAY,
    'items_excluded': TEST_ITEMS_EXCLUDED,
    'extra_categories': TEST_EXTRA_CATEGORIES,
    'languages': TEST_LANGUAGES,
    'hard_of_hearing': '',
    'child_name': TEST_CHILD_NAME,
    'parent_email': TEST_PARENT_EMAIL,
    'mcdi_type': TEST_MCDI_TYPE
}
SEND_FORM_DATA_TEMPLATE_MODIFIED = {
    'global_id': TEST_DB_ID_MOD,
    'study_id': TEST_STUDY_ID_MOD,
    'study': TEST_STUDY_MOD,
    'gender': constants.FEMALE,
    'birthday': TEST_BIRTHDAY_MOD,
    'items_excluded': TEST_ITEMS_EXCLUDED_MOD,
    'extra_categories': TEST_EXTRA_CATEGORIES_MOD,
    'languages': TEST_MOD_LANGUAGES,
    'hard_of_hearing': constants.FORM_SELECTED_VALUE,
    'child_name': TEST_CHILD_NAME_MOD,
    'parent_email': TEST_PARENT_EMAIL_MOD,
    'mcdi_type': TEST_MCDI_TYPE
}
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
    TEST_HARD_OF_HEARING
)
PARENT_MCDI_FORM_URL = '/base/parent_mcdi/%d' % TEST_PARENT_FORM_ID
TEMPLATE_WORD_SPOKEN_VALUES = {
    'cat_1_word_1_report': 1,
    'cat_1_word_2_report': 1,
    'cat_1_word_3_report': 1,
    'cat_2_word_1_report': 1,
    'cat_2_word_2_report': 0,
    'cat_2_word_3_report': 1
}
TEST_PERCENTILE = 50
TEST_PERCENTILE_CLASS = collections.namedtuple('TestPercentileTable',
    ['details'])
TEST_PERCENTILE_TABLE = TEST_PERCENTILE_CLASS('test details')
TODAY = date.today()
TEST_SESSION_NUM = 1
TEST_WORDS_SPOKEN = 5
TEST_AGE = 21
EXPECTED_SNAPSHOT = models.SnapshotMetadata(
    None,
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    TEST_AGE,
    TEST_BIRTHDAY,
    TODAY.strftime('%Y/%m/%d'),
    TEST_SESSION_NUM,
    TEST_SESSION_NUM,
    TEST_WORDS_SPOKEN,
    TEST_ITEMS_EXCLUDED,
    TEST_PERCENTILE,
    TEST_EXTRA_CATEGORIES,
    0,
    TEST_LANGUAGES.split('.'),
    TEST_NUM_LANGUAGES,
    'multilingual-test',
    constants.EXPLICIT_FALSE
)
EXPECTED_SNAPSHOT_MOD = models.SnapshotMetadata(
    None,
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    TEST_AGE,
    TEST_BIRTHDAY_MOD,
    TODAY.strftime('%Y/%m/%d'),
    TEST_SESSION_NUM,
    TEST_SESSION_NUM,
    TEST_WORDS_SPOKEN,
    TEST_ITEMS_EXCLUDED_MOD,
    TEST_PERCENTILE,
    TEST_EXTRA_CATEGORIES_MOD,
    0,
    TEST_LANGUAGES.split('.'),
    TEST_NUM_LANGUAGES,
    'multilingual-test',
    constants.EXPLICIT_FALSE
)
TEMPLATE_WORD_SPOKEN_RECORD = dict(map(
    lambda (word, val): (word.replace('_report', ''), val),
    TEMPLATE_WORD_SPOKEN_VALUES.items()
))
TESTING_SNAPSHOT_CONTENT = collections.namedtuple('TestSnapshotContent',
    ['word', 'value'])
ONE_WORD_KNOWN_SNAPSHOT_CONTENTS = [
    TESTING_SNAPSHOT_CONTENT('cat_1_word_1', constants.EXPLICIT_TRUE),
    TESTING_SNAPSHOT_CONTENT('cat_1_word_2', constants.EXPLICIT_FALSE),
    TESTING_SNAPSHOT_CONTENT('cat_1_word_3', constants.EXPLICIT_FALSE)
]
TWO_WORD_KNOWN_SNAPSHOT_CONTENTS = [
    TESTING_SNAPSHOT_CONTENT('cat_1_word_1', constants.EXPLICIT_TRUE),
    TESTING_SNAPSHOT_CONTENT('cat_1_word_2', constants.EXPLICIT_TRUE),
    TESTING_SNAPSHOT_CONTENT('cat_1_word_3', constants.EXPLICIT_FALSE)
]


class TestEditParentControllers(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.app = daxlabbase.app
        self.app.debug = True

    def test_send_mcdi_form_missing_params(self):
        self.mox.StubOutWithMock(user_util, 'get_user')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['global_id'] = ''
            data['study_id'] = ''
            client.post('/base/parent_accounts', data=data)
            
            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(constants.ERROR_ATTR, '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['global_id'] = ''
            data['study'] = ''
            client.post('/base/parent_accounts', data=data)
            
            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(constants.ERROR_ATTR, '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

    def test_send_mcdi_form_invalid_params(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')

        # Ensure these are not called
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(parent_account_util, 'send_mcdi_email')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model('invalid_format').AndReturn(None)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['mcdi_type'] = 'invalid_format'
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['parent_email'] = 'bad email address'
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['global_id'] = 'invalid'
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['gender'] = -1234
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            data = copy.copy(SEND_FORM_DATA_TEMPLATE)
            data['birthday'] = 'invalid birthday'
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

    def test_send_mcdi_minimum_params(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(parent_account_util, 'send_mcdi_email')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_PARENT_FORM)
        parent_account_util.send_mcdi_email(EXPECTED_PARENT_FORM)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_PARENT_FORM)
        parent_account_util.send_mcdi_email(EXPECTED_PARENT_FORM)

        self.mox.ReplayAll()

        minimal_data_template = copy.copy(SEND_FORM_DATA_TEMPLATE)
        minimal_data_template['gender'] = ''
        minimal_data_template['birthday'] = ''
        minimal_data_template['items_excluded'] = ''
        minimal_data_template['extra_categories'] = ''
        minimal_data_template['languages'] = ''
        minimal_data_template['hard_of_hearing'] = ''

        with self.app.test_client() as client:

            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            data = copy.copy(minimal_data_template)
            del data['study_id']
            del data['study']
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertFalse(constants.ERROR_ATTR in sess)
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)
                self.assertNotEqual(sess[constants.CONFIRMATION_ATTR], '')
                sess[constants.CONFIRMATION_ATTR] = ''

            data = copy.copy(minimal_data_template)
            del data['global_id']
            client.post('/base/parent_accounts', data=data)

            with client.session_transaction() as sess:
                self.assertFalse(constants.ERROR_ATTR in sess)
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)
                self.assertNotEqual(sess[constants.CONFIRMATION_ATTR], '')
                sess[constants.CONFIRMATION_ATTR] = ''

    def test_send_mcdi_all_params(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(parent_account_util, 'send_mcdi_email')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID_MOD)
        db_util.load_mcdi_model(TEST_MCDI_TYPE).AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_MODIFIED_PARENT_FORM)
        parent_account_util.send_mcdi_email(EXPECTED_MODIFIED_PARENT_FORM)

        self.mox.ReplayAll()

        with self.app.test_client() as client:

            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            client.post(
                '/base/parent_accounts',
                data=SEND_FORM_DATA_TEMPLATE_MODIFIED
            )

            with client.session_transaction() as sess:
                self.assertFalse(constants.ERROR_ATTR in sess)
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)
                self.assertNotEqual(sess[constants.CONFIRMATION_ATTR], '')
                sess[constants.CONFIRMATION_ATTR] = ''

    def test_handle_parent_mcdi_form_bad_id(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(None)

        parent_form_no_db_id = copy.copy(EXPECTED_PARENT_FORM)
        parent_form_no_db_id.database_id = None
        user_util.get_user(None).AndReturn(None)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            parent_form_no_db_id)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([])

        parent_form_no_study_id = copy.copy(EXPECTED_PARENT_FORM)
        parent_form_no_study_id.study_id = None
        user_util.get_user(None).AndReturn(None)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            parent_form_no_study_id)
        parent_account_util.get_snapshot_chronology_for_study_id(
            TEST_STUDY, TEST_STUDY_ID).AndReturn([])

        parent_form_no_ids = copy.copy(EXPECTED_PARENT_FORM)
        parent_form_no_ids.study_id = None
        parent_form_no_ids.database_id = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            parent_form_no_ids)

        # Should not be called
        self.mox.StubOutWithMock(db_util, 'insert_snapshot')
        self.mox.StubOutWithMock(db_util, 'remove_parent_form')

        self.mox.ReplayAll()

        with self.app.test_client() as client:

            # Testing with unexpected form ID
            resp = client.post(PARENT_MCDI_FORM_URL)
            self.assertEqual(resp.status_code, 404)

            # Testing with invalid study id
            client.post(PARENT_MCDI_FORM_URL)
            self.assertEqual(resp.status_code, 404)

            # Testing with invalid global id
            client.post(PARENT_MCDI_FORM_URL)
            self.assertEqual(resp.status_code, 404)

            # Testing with no IDs
            client.post(PARENT_MCDI_FORM_URL)
            self.assertEqual(resp.status_code, 404)

    def test_handle_parent_mcdi_form_bad_input(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')

        no_birthday_form = copy.copy(EXPECTED_PARENT_FORM)
        no_birthday_form.birthday = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            no_birthday_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        no_gender_form = copy.copy(EXPECTED_PARENT_FORM)
        no_gender_form.gender = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            no_gender_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        missing_items_excluded_form = copy.copy(EXPECTED_PARENT_FORM)
        missing_items_excluded_form.items_excluded = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            missing_items_excluded_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            missing_items_excluded_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        missing_extra_categories_form = copy.copy(EXPECTED_PARENT_FORM)
        missing_extra_categories_form.extra_categories = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            missing_extra_categories_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            missing_extra_categories_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        no_languages_form = copy.copy(EXPECTED_PARENT_FORM)
        no_languages_form.languages = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            no_languages_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            no_languages_form)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])

        self.mox.ReplayAll()

        with self.app.test_client() as client:

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'birthday': 'invalid birthday'
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'gender': 'invalid gender'
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'items_excluded': 'invalid items excluded'
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'items_excluded': -1
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'extra_categories': 'invalid items excluded'
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'extra_categories': -1
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL)

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            resp = client.post(PARENT_MCDI_FORM_URL, data={
                'languages': ''
            })

            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

    def test_missing_word_value(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        self.mox.ReplayAll()

        word_data_1 = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
        del word_data_1['cat_1_word_1_report']
        word_data_2 = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
        del word_data_2['cat_2_word_3_report']

        with self.app.test_client() as client:

            client.post(PARENT_MCDI_FORM_URL, data=word_data_1)
            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

            client.post(PARENT_MCDI_FORM_URL, data=word_data_2)
            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

    def test_invalid_word_value(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        self.mox.ReplayAll()

        word_data = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
        word_data['cat_2_word_1_report'] = 'test invalid value'

        with self.app.test_client() as client:

            client.post(PARENT_MCDI_FORM_URL, data=word_data)
            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

    def test_invalid_percentile_table(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_percentile_model')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        db_util.load_percentile_model(MALE_TEST_PERCENTILE_NAME).AndReturn(
            None)

        self.mox.ReplayAll()

        with self.app.test_client() as client:

            client.post(PARENT_MCDI_FORM_URL, data=TEMPLATE_WORD_SPOKEN_VALUES)
            with client.session_transaction() as sess:
                self.assertTrue(constants.ERROR_ATTR in sess)
                self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                sess[constants.ERROR_ATTR] = ''
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)

    def test_submit_parent_form_no_params(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_percentile_model')
        self.mox.StubOutWithMock(interp_util, 'monthdelta')
        self.mox.StubOutWithMock(math_util, 'find_percentile')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_snapshot')
        self.mox.StubOutWithMock(db_util, 'remove_parent_form')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        db_util.load_percentile_model(MALE_TEST_PERCENTILE_NAME).AndReturn(
            TEST_PERCENTILE_TABLE)

        interp_util.monthdelta(TEST_BIRTHDAY_DATE, TODAY).AndReturn(TEST_AGE)
        
        math_util.find_percentile(
            'test details',
            TEST_WORDS_SPOKEN,
            TEST_AGE,
            6
        ).AndReturn(TEST_PERCENTILE)
        
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn([])

        word_values = dict(map(
            lambda (word, val): (word.replace('_report', ''), val),
            TEMPLATE_WORD_SPOKEN_VALUES.items()
        ))
        db_util.insert_snapshot(EXPECTED_SNAPSHOT, mox.IsA(dict))
        db_util.remove_parent_form(str(TEST_PARENT_FORM_ID))

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            client.post(PARENT_MCDI_FORM_URL, data=TEMPLATE_WORD_SPOKEN_VALUES)

    def test_submit_parent_form_missing_record(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_percentile_model')
        self.mox.StubOutWithMock(interp_util, 'monthdelta')
        self.mox.StubOutWithMock(math_util, 'find_percentile')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_snapshot')
        self.mox.StubOutWithMock(db_util, 'remove_parent_form')

        partial_parent_form = copy.copy(EXPECTED_PARENT_FORM)
        partial_parent_form.items_excluded = None
        partial_parent_form.extra_categories = None
        partial_parent_form.child_name = None
        partial_parent_form.parent_email = None
        partial_parent_form.birthday = None
        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            partial_parent_form)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        db_util.load_percentile_model(MALE_TEST_PERCENTILE_NAME).AndReturn(
            TEST_PERCENTILE_TABLE)

        interp_util.monthdelta(TEST_BIRTHDAY_DATE_MOD, TODAY).AndReturn(
            TEST_AGE)
        
        math_util.find_percentile(
            'test details',
            TEST_WORDS_SPOKEN,
            TEST_AGE,
            6
        ).AndReturn(TEST_PERCENTILE)
        
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn([])

        word_values = dict(map(
            lambda (word, val): (word.replace('_report', ''), val),
            TEMPLATE_WORD_SPOKEN_VALUES.items()
        ))
        db_util.insert_snapshot(EXPECTED_SNAPSHOT_MOD, mox.IsA(dict))
        db_util.remove_parent_form(str(TEST_PARENT_FORM_ID))

        self.mox.ReplayAll()

        data = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
        data['items_excluded'] = TEST_ITEMS_EXCLUDED_MOD
        data['extra_categories'] = TEST_EXTRA_CATEGORIES_MOD
        data['child_name'] = TEST_CHILD_NAME_MOD
        data['parent_email'] = TEST_PARENT_EMAIL_MOD
        data['birthday'] = TEST_BIRTHDAY_MOD
        TEMPLATE_WORD_SPOKEN_VALUES
        
        with self.app.test_client() as client:
            client.post(PARENT_MCDI_FORM_URL, data=data)

            with client.session_transaction() as sess:
                self.assertFalse(constants.ERROR_ATTR in sess)
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)

    def test_submit_parent_form_favor_record_values(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_study_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_percentile_model')
        self.mox.StubOutWithMock(interp_util, 'monthdelta')
        self.mox.StubOutWithMock(math_util, 'find_percentile')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_snapshot')
        self.mox.StubOutWithMock(db_util, 'remove_parent_form')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn([TEST_SNAPSHOT])
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        db_util.load_percentile_model(MALE_TEST_PERCENTILE_NAME).AndReturn(
            TEST_PERCENTILE_TABLE)

        interp_util.monthdelta(TEST_BIRTHDAY_DATE, TODAY).AndReturn(
            TEST_AGE)
        
        math_util.find_percentile(
            'test details',
            TEST_WORDS_SPOKEN,
            TEST_AGE,
            6
        ).AndReturn(TEST_PERCENTILE)
        
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn([])

        db_util.insert_snapshot(EXPECTED_SNAPSHOT, TEMPLATE_WORD_SPOKEN_RECORD)
        db_util.remove_parent_form(str(TEST_PARENT_FORM_ID))

        self.mox.ReplayAll()

        data = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
        data['items_excluded'] = TEST_ITEMS_EXCLUDED_MOD
        data['extra_categories'] = TEST_EXTRA_CATEGORIES_MOD
        data['child_name'] = TEST_CHILD_NAME
        data['parent_email'] = TEST_PARENT_EMAIL
        data['birthday'] = TEST_BIRTHDAY_MOD
        TEMPLATE_WORD_SPOKEN_VALUES
        
        with self.app.test_client() as client:
            client.post(PARENT_MCDI_FORM_URL, data=data)

            with client.session_transaction() as sess:
                self.assertFalse(constants.ERROR_ATTR in sess)
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)

    def test_fill_parent_form_previous_snapshot(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(parent_account_util,
            'get_snapshot_chronology_for_db_id')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_snapshot_contents')

        db_util.get_parent_form_by_id(str(TEST_PARENT_FORM_ID)).AndReturn(
            EXPECTED_PARENT_FORM)
        chronology = copy.deepcopy([EXPECTED_SNAPSHOT, EXPECTED_SNAPSHOT_MOD])
        chronology[0].database_id = 1
        chronology[1].database_id = 2
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        user_util.get_user(None).AndReturn(None)
        parent_account_util.get_snapshot_chronology_for_db_id(
            TEST_DB_ID).AndReturn(chronology)
        db_util.load_snapshot_contents(chronology[0]).AndReturn(
            TWO_WORD_KNOWN_SNAPSHOT_CONTENTS)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            form = client.get(PARENT_MCDI_FORM_URL).data
            self.assertEqual(form.count('"1" checked'), 2)
            self.assertEqual(form.count('"0" checked'), 4)
