"""Automated tests for soliciting and managing parent input.

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
import collections
import copy
from datetime import date
import unittest
import unittest.mock

import cdibase
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import math_util
from ..util import parent_account_util
from ..util import user_util
from ..struct import models

TEST_CDI_TYPE = 'standard'
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
TEST_BIRTHDAY = '09/12/2011'
TEST_BIRTHDAY_ISO = '2011/09/12'
TEST_BIRTHDAY_DATE = date(2011, 9, 12)
TEST_PARENT_FORM_ID_MOD = 30
TEST_CHILD_NAME_MOD = 'Test Child2'
TEST_PARENT_EMAIL_MOD = 'parent2@example.com'
TEST_DB_ID_MOD = 321
TEST_STUDY_ID_MOD = 654
TEST_STUDY_MOD = 'test study 2'
TEST_BIRTHDAY_MOD = '09/13/2011'
TEST_BIRTHDAY_ISO_MOD = '2011/09/13'
TEST_BIRTHDAY_DATE_MOD = date(2011, 9, 13)
TEST_ITEMS_EXCLUDED_MOD = 7
TEST_EXTRA_CATEGORIES_MOD = 8
TEST_NUM_LANGUAGES_MOD = 1
TEST_USER = models.User(
    TEST_DB_ID,
    TEST_EMAIL,
    None,
    False,
    False,
    False,
    True,
    False,
    True,
    False,
    False
)
TEST_API_KEY = 'abc123'
TEST_API_KEY_ENTRY = models.APIKey(
    TEST_EMAIL,
    TEST_API_KEY
)
MALE_TEST_PERCENTILE_NAME = 'male_test_percentiles'
FEMALE_TEST_PERCENTILE_NAME = 'female_test_percentiles'
OTHER_TEST_PERCENTILE_NAME = 'other_test_percentiles'
TEST_FORMAT = models.CDIFormat(
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
        'meta': {'cdi_type': 'multilingual-test'}
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
    TEST_BIRTHDAY_ISO,
    TEST_ITEMS_EXCLUDED,
    TEST_EXTRA_CATEGORIES,
    'english,spanish',
    TEST_NUM_LANGUAGES,
    constants.EXPLICIT_FALSE,
    0
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
    TEST_BIRTHDAY_ISO_MOD,
    TEST_ITEMS_EXCLUDED_MOD,
    TEST_EXTRA_CATEGORIES_MOD,
    TEST_MOD_LANGUAGES,
    TEST_MOD_NUM_LANGUAGES,
    constants.EXPLICIT_TRUE,
    0
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
    'cdi_type': TEST_CDI_TYPE
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
    'cdi_type': TEST_CDI_TYPE
}
TEST_SNAPSHOT = models.SnapshotMetadata(
    TEST_SNAPSHOT_ID,
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    24,
    TEST_BIRTHDAY_ISO,
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
PARENT_CDI_FORM_URL = '/base/parent_cdi/%d' % TEST_PARENT_FORM_ID
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
    TEST_BIRTHDAY_ISO,
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
    constants.EXPLICIT_FALSE,
    False
)
EXPECTED_SNAPSHOT_MOD = models.SnapshotMetadata(
    None,
    TEST_DB_ID,
    TEST_STUDY_ID,
    TEST_STUDY,
    constants.MALE,
    TEST_AGE,
    TEST_BIRTHDAY_ISO_MOD,
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
    constants.EXPLICIT_FALSE,
    False
)
TEMPLATE_WORD_SPOKEN_RECORD = dict(map(
    lambda x: (x[0].replace('_report', ''), x[1]),
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


class TestEditParentControllers(unittest.TestCase):

    def setUp(self):
        self.app = cdibase.app
        self.app.debug = True
        self.__callback_called = False

    def __run_with_mocks(self, on_start, body, on_end):
        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.parent_account_util.generate_unique_cdi_form_id') as mock_generate_unique_cdi_form_id:
                with unittest.mock.patch('prog_code.util.db_util.load_cdi_model') as mock_load_cdi_model:
                    with unittest.mock.patch('prog_code.util.filter_util.run_search_query') as mock_run_search_query:
                        with unittest.mock.patch('prog_code.util.db_util.insert_parent_form') as mock_insert_parent_form:
                            with unittest.mock.patch('prog_code.util.parent_account_util.send_cdi_email') as mock_send_cdi_email:
                                with unittest.mock.patch('prog_code.util.db_util.insert_snapshot') as mock_insert_snapshot:
                                    with unittest.mock.patch('prog_code.util.db_util.remove_parent_form') as mock_remove_parent_form:
                                        with unittest.mock.patch('prog_code.util.db_util.get_parent_form_by_id') as mock_get_parent_form_by_id:
                                            with unittest.mock.patch('prog_code.util.db_util.load_percentile_model') as mock_load_percentile_model:
                                                with unittest.mock.patch('prog_code.util.parent_account_util.get_snapshot_chronology_for_db_id') as mock_get_snapshot_chronology_for_db_id:
                                                    with unittest.mock.patch('prog_code.util.interp_util.monthdelta') as mock_monthdelta:
                                                        with unittest.mock.patch('prog_code.util.math_util.find_percentile') as mock_find_percentile:
                                                            with unittest.mock.patch('prog_code.util.db_util.load_snapshot_contents') as mock_load_snapshot_contents:
                                                                mocks = {
                                                                    'get_user': mock_get_user,
                                                                    'generate_unique_cdi_form_id': mock_generate_unique_cdi_form_id,
                                                                    'load_cdi_model': mock_load_cdi_model,
                                                                    'run_search_query': mock_run_search_query,
                                                                    'insert_parent_form': mock_insert_parent_form,
                                                                    'send_cdi_email': mock_send_cdi_email,
                                                                    'insert_snapshot': mock_insert_snapshot,
                                                                    'remove_parent_form': mock_remove_parent_form,
                                                                    'get_parent_form_by_id': mock_get_parent_form_by_id,
                                                                    'load_percentile_model': mock_load_percentile_model,
                                                                    'get_snapshot_chronology_for_db_id': mock_get_snapshot_chronology_for_db_id,
                                                                    'monthdelta': mock_monthdelta,
                                                                    'find_percentile': mock_find_percentile,
                                                                    'load_snapshot_contents': mock_load_snapshot_contents
                                                                }
                                                                on_start(mocks)
                                                                body()
                                                                on_end(mocks)
                                                                self.__callback_called = True

    def __assert_callback(self):
        self.assertTrue(self.__callback_called)

    def __run_with_standard_mocks(self, body):
        self.__run_with_mocks(
            lambda mocks: self.__standard_on_start(mocks),
            body,
            lambda mocks: self.__standard_on_end(mocks)
        )

    def __standard_on_start(self, mocks):
        mocks['get_parent_form_by_id'].return_value = EXPECTED_PARENT_FORM
        mocks['load_cdi_model'].return_value = TEST_FORMAT

    def __standard_on_end(self, mocks):
        mocks['get_parent_form_by_id'].assert_called_with(
            str(TEST_PARENT_FORM_ID)
        )
        mocks['load_cdi_model'].assert_called_with('standard')

    def test_send_cdi_form_missing_params(self):
        def body():
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

        def on_start(mocks):
            mocks['get_user'].return_value = TEST_USER

        def on_end(mocks):
            mocks['get_user'].assert_called_with(TEST_EMAIL)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_cdi_form_invalid_params(self):

        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                data = copy.copy(SEND_FORM_DATA_TEMPLATE)
                data['cdi_type'] = 'invalid_format'
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

        def on_start(mocks):
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_cdi_model'].side_effect = [
                None,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT
            ]

        def on_end(mocks):
            mocks['run_search_query'].assert_not_called()
            mocks['insert_parent_form'].assert_not_called()
            mocks['send_cdi_email'].assert_not_called()

            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_cdi_model'].assert_any_call('invalid_format')
            mocks['load_cdi_model'].assert_any_call(TEST_CDI_TYPE)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_cdi_minimum_params(self):

        def body():
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

        def on_start(mocks):
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]

        def on_end(mocks):
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_cdi_model'].assert_called_with(TEST_CDI_TYPE)
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )

            self.assertEqual(len(mocks['insert_parent_form'].mock_calls), 2)
            mocks['insert_parent_form'].assert_called_with(EXPECTED_PARENT_FORM)

            self.assertEqual(len(mocks['send_cdi_email'].mock_calls), 2)
            mocks['send_cdi_email'].assert_called_with(EXPECTED_PARENT_FORM)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_cdi_all_params(self):
        def body():
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

        def on_start(mocks):
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID_MOD
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]

        def on_end(mocks):
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_cdi_model'].assert_called_with(TEST_CDI_TYPE)
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_parent_form'].assert_called_with(EXPECTED_MODIFIED_PARENT_FORM)
            mocks['send_cdi_email'].assert_called_with(EXPECTED_MODIFIED_PARENT_FORM)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_handle_parent_cdi_form_bad_id(self):
        def body():
            with self.app.test_client() as client:

                # Testing with unexpected form ID
                resp = client.post(PARENT_CDI_FORM_URL)
                self.assertEqual(resp.status_code, 404)

                # Testing with invalid study id
                client.post(PARENT_CDI_FORM_URL)
                self.assertEqual(resp.status_code, 404)

                # Testing with invalid global id
                client.post(PARENT_CDI_FORM_URL)
                self.assertEqual(resp.status_code, 404)

                # Testing with no IDs
                client.post(PARENT_CDI_FORM_URL)
                self.assertEqual(resp.status_code, 404)

        def on_start(mocks):
            parent_form_no_db_id = copy.copy(EXPECTED_PARENT_FORM)
            parent_form_no_db_id.database_id = None

            parent_form_no_study_id = copy.copy(EXPECTED_PARENT_FORM)
            parent_form_no_study_id.study_id = None

            parent_form_no_ids = copy.copy(EXPECTED_PARENT_FORM)
            parent_form_no_ids.study_id = None
            parent_form_no_ids.database_id = None

            mocks['get_user'].return_value = None
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['get_parent_form_by_id'].side_effect = [
                None,
                parent_form_no_db_id,
                parent_form_no_study_id,
                parent_form_no_ids
            ]

        def on_end(mocks):
            mocks['get_user'].assert_called_with(None)
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['insert_snapshot'].assert_not_called()
            mocks['remove_parent_form'].assert_not_called()

            mocks['get_parent_form_by_id'].assert_called_with(str(TEST_PARENT_FORM_ID))
            self.assertEqual(
                len(mocks['get_parent_form_by_id'].mock_calls),
                4
            )

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_handle_parent_cdi_form_bad_input(self):
        def body():
            with self.app.test_client() as client:

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'birthday': 'invalid birthday'
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'gender': 'invalid gender'
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'items_excluded': 'invalid items excluded'
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'items_excluded': -1
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'extra_categories': 'invalid items excluded'
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'extra_categories': -1
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL)

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                resp = client.post(PARENT_CDI_FORM_URL, data={
                    'languages': ''
                })

                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

        def on_start(mocks):
            no_birthday_form = copy.copy(EXPECTED_PARENT_FORM)
            no_birthday_form.birthday = None

            no_gender_form = copy.copy(EXPECTED_PARENT_FORM)
            no_gender_form.gender = None

            missing_items_excluded_form = copy.copy(EXPECTED_PARENT_FORM)
            missing_items_excluded_form.items_excluded = None

            missing_extra_categories_form = copy.copy(EXPECTED_PARENT_FORM)
            missing_extra_categories_form.extra_categories = None

            no_languages_form = copy.copy(EXPECTED_PARENT_FORM)
            no_languages_form.languages = None

            mocks['get_parent_form_by_id'].side_effect = [
                no_birthday_form,
                no_gender_form,
                missing_items_excluded_form,
                missing_items_excluded_form,
                missing_extra_categories_form,
                missing_extra_categories_form,
                no_languages_form,
                no_languages_form
            ]
            mocks['load_cdi_model'].return_value = TEST_FORMAT

        def on_end(mocks):
            self.assertEqual(
                len(mocks['get_parent_form_by_id'].mock_calls),
                8
            )
            mocks['get_parent_form_by_id'].assert_called_with(
                str(TEST_PARENT_FORM_ID)
            )

            self.assertEqual(
                len(mocks['load_cdi_model'].mock_calls),
                8
            )
            mocks['load_cdi_model'].assert_called_with('standard')

            mocks['load_percentile_model'].assert_not_called()
            mocks['insert_snapshot'].assert_not_called()
            mocks['remove_parent_form'].assert_not_called()

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_missing_word_value(self):
        def body():
            word_data_1 = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
            del word_data_1['cat_1_word_1_report']
            word_data_2 = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
            del word_data_2['cat_2_word_3_report']

            with self.app.test_client() as client:

                client.post(PARENT_CDI_FORM_URL, data=word_data_1)
                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

                client.post(PARENT_CDI_FORM_URL, data=word_data_2)
                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

        self.__run_with_standard_mocks(body)
        self.__assert_callback()

    def test_invalid_word_value(self):
        def body():
            word_data = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
            word_data['cat_2_word_1_report'] = 'test invalid value'

            with self.app.test_client() as client:

                client.post(PARENT_CDI_FORM_URL, data=word_data)
                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

        self.__run_with_standard_mocks(body)
        self.__assert_callback()

    def test_invalid_percentile_table(self):
        def body():
            with self.app.test_client() as client:

                client.post(PARENT_CDI_FORM_URL, data=TEMPLATE_WORD_SPOKEN_VALUES)
                with client.session_transaction() as sess:
                    self.assertTrue(constants.ERROR_ATTR in sess)
                    self.assertNotEqual(sess[constants.ERROR_ATTR], '')
                    sess[constants.ERROR_ATTR] = ''
                    self.assertFalse(constants.CONFIRMATION_ATTR in sess)

        def on_start(mocks):
            mocks['get_parent_form_by_id'].return_value = EXPECTED_PARENT_FORM
            mocks['get_snapshot_chronology_for_db_id'].return_value = TEST_DB_ID
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['load_percentile_model'].return_value = None

        def on_end(mocks):
            mocks['get_parent_form_by_id'].assert_called_with(str(TEST_PARENT_FORM_ID))
            mocks['get_snapshot_chronology_for_db_id'].assert_called_with(TEST_DB_ID)
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['load_percentile_model'].assert_called_with(MALE_TEST_PERCENTILE_NAME)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_submit_parent_form_no_params(self):
        def body():
            with self.app.test_client() as client:
                client.post(PARENT_CDI_FORM_URL, data=TEMPLATE_WORD_SPOKEN_VALUES)

        def on_start(mocks):
            word_values = dict(map(
                lambda x: (x[0].replace('_report', ''), x[1]),
                TEMPLATE_WORD_SPOKEN_VALUES.items()
            ))

            mocks['get_parent_form_by_id'].return_value = EXPECTED_PARENT_FORM
            mocks['get_snapshot_chronology_for_db_id'].return_value = [TEST_SNAPSHOT]
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['load_percentile_model'].return_value = TEST_PERCENTILE_TABLE
            mocks['monthdelta'].return_value = TEST_AGE
            mocks['find_percentile'].return_value = TEST_PERCENTILE

        def on_end(mocks):
            mocks['get_parent_form_by_id'].assert_called_with(
                str(TEST_PARENT_FORM_ID)
            )
            mocks['get_snapshot_chronology_for_db_id'].assert_called_with(
                TEST_DB_ID
            )
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['load_percentile_model'].assert_called_with(
                MALE_TEST_PERCENTILE_NAME
            )
            mocks['monthdelta'].assert_called_with(TEST_BIRTHDAY_DATE, TODAY)
            mocks['find_percentile'].assert_called_with(
                'test details',
                TEST_WORDS_SPOKEN,
                TEST_AGE,
                6
            )
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_snapshot'].assert_called_with(
                EXPECTED_SNAPSHOT,
                unittest.mock.ANY
            )
            mocks['remove_parent_form'].assert_called_with(
                str(TEST_PARENT_FORM_ID)
            )

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_submit_parent_form_missing_record(self):
        def body():
            data = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
            data['items_excluded'] = TEST_ITEMS_EXCLUDED_MOD
            data['extra_categories'] = TEST_EXTRA_CATEGORIES_MOD
            data['child_name'] = TEST_CHILD_NAME_MOD
            data['parent_email'] = TEST_PARENT_EMAIL_MOD
            data['birthday'] = TEST_BIRTHDAY_MOD

            with self.app.test_client() as client:
                client.post(PARENT_CDI_FORM_URL, data=data)

                with client.session_transaction() as sess:
                    self.assertFalse(constants.ERROR_ATTR in sess)
                    self.assertTrue(constants.CONFIRMATION_ATTR in sess)

        def on_start(mocks):
            partial_parent_form = copy.copy(EXPECTED_PARENT_FORM)
            partial_parent_form.items_excluded = None
            partial_parent_form.extra_categories = None
            partial_parent_form.child_name = None
            partial_parent_form.parent_email = None
            partial_parent_form.birthday = None

            word_values = dict(map(
                lambda x: (x[0].replace('_report', ''), x[1]),
                TEMPLATE_WORD_SPOKEN_VALUES.items()
            ))

            mocks['get_parent_form_by_id'].return_value = partial_parent_form
            mocks['get_snapshot_chronology_for_db_id'].return_value = [TEST_SNAPSHOT]
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['load_percentile_model'].return_value = TEST_PERCENTILE_TABLE
            mocks['monthdelta'].return_value = TEST_AGE
            mocks['find_percentile'].return_value = TEST_PERCENTILE
            mocks['run_search_query'].return_value = []

        def on_end(mocks):
            mocks['get_parent_form_by_id'].assert_called_with(str(TEST_PARENT_FORM_ID))
            mocks['get_snapshot_chronology_for_db_id'].assert_called_with(TEST_DB_ID)
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['load_percentile_model'].assert_called_with(MALE_TEST_PERCENTILE_NAME)
            mocks['monthdelta'].assert_called_with(TEST_BIRTHDAY_DATE_MOD, TODAY)
            mocks['find_percentile'].assert_called_with(
                'test details',
                TEST_WORDS_SPOKEN,
                TEST_AGE,
                6
            )
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_snapshot'].assert_called_with(
                EXPECTED_SNAPSHOT_MOD,
                unittest.mock.ANY
            )
            mocks['remove_parent_form'].assert_called_with(
                str(TEST_PARENT_FORM_ID)
            )

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_submit_parent_form_favor_record_values(self):
        def body():
            data = copy.copy(TEMPLATE_WORD_SPOKEN_VALUES)
            data['items_excluded'] = TEST_ITEMS_EXCLUDED_MOD
            data['extra_categories'] = TEST_EXTRA_CATEGORIES_MOD
            data['child_name'] = TEST_CHILD_NAME
            data['parent_email'] = TEST_PARENT_EMAIL
            data['birthday'] = TEST_BIRTHDAY_MOD

            with self.app.test_client() as client:
                client.post(PARENT_CDI_FORM_URL, data=data)

                with client.session_transaction() as sess:
                    self.assertFalse(constants.ERROR_ATTR in sess)
                    self.assertTrue(constants.CONFIRMATION_ATTR in sess)

        def on_start(mocks):
            mocks['get_parent_form_by_id'].return_value = EXPECTED_PARENT_FORM
            mocks['get_snapshot_chronology_for_db_id'].return_value = [TEST_SNAPSHOT]
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['load_percentile_model'].return_value = TEST_PERCENTILE_TABLE
            mocks['monthdelta'].return_value = TEST_AGE
            mocks['find_percentile'].return_value = TEST_PERCENTILE
            mocks['run_search_query'].return_value = []

        def on_end(mocks):
            mocks['get_parent_form_by_id'].assert_called_with(
                str(TEST_PARENT_FORM_ID)
            )
            mocks['get_snapshot_chronology_for_db_id'].assert_called_with(
                TEST_DB_ID
            )
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['load_percentile_model'].assert_called_with(
                MALE_TEST_PERCENTILE_NAME
            )
            mocks['monthdelta'].assert_called_with(
                TEST_BIRTHDAY_DATE,
                TODAY
            )
            mocks['find_percentile'].assert_called_with('test details',
                TEST_WORDS_SPOKEN,
                TEST_AGE,
                6
            )
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_snapshot'].assert_called_with(
                EXPECTED_SNAPSHOT,
                TEMPLATE_WORD_SPOKEN_RECORD
            )
            mocks['remove_parent_form'].assert_called_with(
                str(TEST_PARENT_FORM_ID)
            )

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_fill_parent_form_previous_snapshot(self):
        self.__chronology = copy.deepcopy([EXPECTED_SNAPSHOT, EXPECTED_SNAPSHOT_MOD])
        self.__chronology[0].database_id = 1
        self.__chronology[1].database_id = 2

        def body():
            with self.app.test_client() as client:
                form = client.get(PARENT_CDI_FORM_URL).data.decode('utf-8')
                self.assertEqual(form.count('"1" checked'), 2)
                self.assertEqual(form.count('"0" checked'), 4)

        def on_start(mocks):
            mocks['get_parent_form_by_id'].return_value = EXPECTED_PARENT_FORM
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['get_user'].return_value = None
            mocks['get_snapshot_chronology_for_db_id'].return_value = self.__chronology
            mocks['load_snapshot_contents'].return_value = TWO_WORD_KNOWN_SNAPSHOT_CONTENTS

        def on_end(mocks):
            mocks['get_parent_form_by_id'].assert_called_with(str(TEST_PARENT_FORM_ID))
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['get_user'].assert_called_with(None)
            mocks['get_snapshot_chronology_for_db_id'].assert_called_with(TEST_DB_ID)
            mocks['load_snapshot_contents'].assert_called_with(self.__chronology[0])

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()
