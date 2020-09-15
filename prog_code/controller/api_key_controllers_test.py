"""Tests for logic used in generating and managing user API keys.

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
import json
import math
import unittest
import urllib

import cdibase
from ..controller import api_key_controllers
from ..struct import models
from ..util import api_key_util
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import parent_account_util
from ..util import report_util
from ..util import session_util
from ..util import user_util

INTEGER_FIELDS = api_key_controllers.INTEGER_FIELDS
FLOAT_FIELDS = api_key_controllers.FLOAT_FIELDS
SPECIAL_API_QUERY_FIELDS = api_key_controllers.SPECIAL_API_QUERY_FIELDS

TEST_PARENT_FORM_ID = 20
TEST_CHILD_NAME = 'Test Child'
TEST_PARENT_EMAIL = 'parent@example.com'
TEST_EMAIL = 'test_mail'
TEST_DB_ID = 123
TEST_STUDY_ID = 456
TEST_SNAPSHOT_ID = 789
TEST_ITEMS_EXCLUDED = 3
TEST_EXTRA_CATEGORIES = 4
TEST_LANGUAGES = 'english.spanish'
TEST_NUM_LANGUAGES = 2
TEST_HARD_OF_HEARING = constants.EXPLICIT_FALSE
TEST_STUDY = 'test study'
TEST_BIRTHDAY = '2011/09/12'
TEST_PARENT_FORM_ID_MOD = 30
TEST_CHILD_NAME_MOD = 'Test Child2'
TEST_PARENT_EMAIL_MOD = 'parent2@example.com'
TEST_DB_ID_MOD = 321
TEST_STUDY_ID_MOD = 654
TEST_STUDY_MOD = 'test study 2'
TEST_BIRTHDAY_MOD = '2011/09/13'
TEST_BIRTHDAY_MOD_ISO = '2011-09-13'
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
    True,
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
    TEST_HARD_OF_HEARING,
    False
)
TEST_FORMAT = models.CDIFormat(
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
    constants.EXPLICIT_FALSE,
    12
)
EXPECTED_MODIFIED_PARENT_FORM = models.ParentForm(
    TEST_PARENT_FORM_ID_MOD,
    TEST_CHILD_NAME_MOD,
    TEST_PARENT_EMAIL_MOD,
    'standard_mod',
    TEST_DB_ID,
    TEST_STUDY_ID_MOD,
    TEST_STUDY_MOD,
    constants.FEMALE,
    TEST_BIRTHDAY_MOD,
    TEST_ITEMS_EXCLUDED_MOD,
    TEST_EXTRA_CATEGORIES_MOD,
    'english',
    TEST_NUM_LANGUAGES_MOD,
    constants.EXPLICIT_TRUE,
    12
)


class TestAPIKeyControllers(unittest.TestCase):

    def setUp(self):
        self.app = cdibase.app
        self.app.debug = True
        self.__callback_called = False

    def __run_with_mocks(self, on_start, body, on_end):
        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.session_util.get_user_id') as mock_get_user_id:
                with unittest.mock.patch('prog_code.util.api_key_util.create_new_api_key') as mock_create_new_api_key:
                    with unittest.mock.patch('prog_code.util.db_util.get_api_key') as mock_get_api_key:
                        with unittest.mock.patch('prog_code.util.db_util.load_cdi_model') as mock_load_cdi_model:
                            with unittest.mock.patch('prog_code.util.db_util.load_presentation_model') as mock_load_presentation_model:
                                with unittest.mock.patch('prog_code.util.parent_account_util.generate_unique_cdi_form_id') as mock_generate_unique_cdi_form_id:
                                    with unittest.mock.patch('prog_code.util.filter_util.run_search_query') as mock_run_search_query:
                                        with unittest.mock.patch('prog_code.util.db_util.insert_parent_form') as mock_insert_parent_form:
                                            with unittest.mock.patch('prog_code.util.report_util.summarize_snapshots') as mock_summarize_snapshots:
                                                mocks = {
                                                    'get_user': mock_get_user,
                                                    'get_user_id': mock_get_user_id,
                                                    'create_new_api_key': mock_create_new_api_key,
                                                    'get_api_key': mock_get_api_key,
                                                    'load_cdi_model': mock_load_cdi_model,
                                                    'load_presentation_model': mock_load_presentation_model,
                                                    'generate_unique_cdi_form_id': mock_generate_unique_cdi_form_id,
                                                    'run_search_query': mock_run_search_query,
                                                    'insert_parent_form': mock_insert_parent_form,
                                                    'summarize_snapshots': mock_summarize_snapshots
                                                }
                                                on_start(mocks)
                                                body()
                                                on_end(mocks)
                                                self.__callback_called = True

    def __assert_callback(self):
        self.assertTrue(self.__callback_called)

    def test_generate_error(self):
        test_message = 'test_message'

        ret_str, status = api_key_controllers.generate_error(test_message,
            TEST_DB_ID)
        self.assertEqual(json.loads(ret_str)[constants.ERROR_ATTR],
            test_message)
        self.assertEqual(status, TEST_DB_ID)

        ret_str, status = api_key_controllers.generate_unauthorized_error(
            test_message)
        self.assertEqual(json.loads(ret_str)[constants.ERROR_ATTR],
            test_message)
        self.assertEqual(status, api_key_controllers.UNAUTHORIZED_STATUS)

        ret_str, status = api_key_controllers.generate_invalid_request_error(
            test_message)
        self.assertEqual(json.loads(ret_str)[constants.ERROR_ATTR],
            test_message)
        self.assertEqual(status, api_key_controllers.INVALID_REQUEST_STATUS)

    def test_make_filter(self):
        filterModel = api_key_controllers.make_filter('test_field', 'test val')
        self.assertEqual(filterModel.field, 'test_field')
        self.assertEqual(filterModel.operand, 'test val')
        self.assertEqual(filterModel.operator, 'eq')

        self.assertIn('min_percentile', FLOAT_FIELDS)
        self.assertIn('min_percentile', SPECIAL_API_QUERY_FIELDS)
        filterModel = api_key_controllers.make_filter('min_percentile', '50')
        self.assertEqual(filterModel.field, 'percentile')
        self.assertTrue(math.fabs(filterModel.operand - 50) < 0.001)

        self.assertIn('child_id', INTEGER_FIELDS)
        filterModel = api_key_controllers.make_filter('child_id', '100')
        self.assertEqual(filterModel.field, 'child_id')
        self.assertEqual(filterModel.operand, 100)
        self.assertEqual(filterModel.operator, 'eq')

    def test_create_api_key(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/config_api_key/new')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertNotEqual(sess[constants.CONFIRMATION_ATTR], '')
                    self.assertFalse(constants.ERROR_ATTR in sess)

        def on_start(mocks):
            mocks['get_user'].return_value = TEST_USER
            mocks['get_user_id'].return_value = TEST_DB_ID

        def on_end(mocks):
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['create_new_api_key'].assert_called_with(TEST_DB_ID)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_verify_api_key_for_parent_forms(self):

        def body():
            problem = api_key_controllers.verify_api_key_for_parent_forms(
                TEST_API_KEY)
            self.assertNotEqual(problem, None)

            problem = api_key_controllers.verify_api_key_for_parent_forms(
                TEST_API_KEY)
            self.assertNotEqual(problem, None)

            problem = api_key_controllers.verify_api_key_for_parent_forms(
                TEST_API_KEY)
            self.assertNotEqual(problem, None)

            problem = api_key_controllers.verify_api_key_for_parent_forms(
                TEST_API_KEY)
            self.assertEqual(problem, None)

        def on_start(mocks):
            mocks['get_api_key'].side_effect = [
                None,
                TEST_API_KEY_ENTRY,
                TEST_API_KEY_ENTRY,
                TEST_API_KEY_ENTRY
            ]

            user_1 = models.User(
                TEST_DB_ID,
                TEST_EMAIL,
                None,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False
            )

            user_2 = models.User(
                TEST_DB_ID,
                TEST_EMAIL,
                None,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False
            )

            user_3 = TEST_USER

            mocks['get_user'].side_effect = [user_1, user_2, user_3]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_form_missing_params(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_form')
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                        urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': 'test parent'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_form_invalid_params(self):

        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'invalid_format',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'format': 'invalid_format',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': 'invalid type'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': 'test',
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': str(TEST_DB_ID),
                        'gender': 'invalid'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': str(TEST_DB_ID),
                        'hard_of_hearing': 'invalid'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': str(TEST_DB_ID),
                        'birthday': 'invalid'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': 'test email',
                        'database_id': str(TEST_DB_ID)
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_presentation_model'].side_effect = [
                TEST_PRESENTATION_FORMAT_METADATA,
                None,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA
            ]
            mocks['load_cdi_model'].side_effect = [
                None,
                None,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT
            ]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)

            self.assertEqual(
                len(mocks['load_presentation_model'].mock_calls),
                8
            )
            mocks['load_presentation_model'].assert_any_call('standard')
            mocks['load_presentation_model'].assert_any_call('invalid_format')

            self.assertEqual(
                len(mocks['load_cdi_model'].mock_calls),
                7
            )
            mocks['load_presentation_model'].assert_any_call('standard')
            mocks['load_presentation_model'].assert_any_call('invalid_format')

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_form_defaults(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': TEST_CHILD_NAME,
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertFalse('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_presentation_model'].return_value = TEST_PRESENTATION_FORMAT_METADATA
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_presentation_model'].assert_called_with('standard')
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_parent_form'].assert_called_with(EXPECTED_PARENT_FORM)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_form_non_defaults(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': TEST_CHILD_NAME_MOD,
                        'cdi_type': 'standard_mod',
                        'parent_email': TEST_PARENT_EMAIL_MOD,
                        'study': TEST_STUDY_MOD,
                        'study_id': TEST_STUDY_ID_MOD,
                        'gender': 'female',
                        'birthday': TEST_BIRTHDAY_MOD_ISO,
                        'items_excluded': TEST_ITEMS_EXCLUDED_MOD,
                        'extra_categories': TEST_EXTRA_CATEGORIES_MOD,
                        'languages': 'english',
                        'hard_of_hearing': 'true',
                        'format': 'standard_mod'
                    })
                )

                self.assertFalse('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID_MOD
            mocks['load_presentation_model'].return_value = TEST_PRESENTATION_FORMAT_METADATA
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_presentation_model'].assert_called_with('standard_mod')
            mocks['load_cdi_model'].assert_called_with('standard_mod')
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_parent_form'].assert_called_with(
                EXPECTED_MODIFIED_PARENT_FORM
            )

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_forms_missing_params(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_forms')
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                        urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': 'test parent'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_forms_invalid_params(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'invalid_format',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'format': 'invalid_format',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': 'invalid type'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': 'test wrong email',
                        'database_id': str(TEST_DB_ID)
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': str(TEST_DB_ID),
                        'gender': 'invalid'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': str(TEST_DB_ID),
                        'hard_of_hearing': 'invalid'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': str(TEST_DB_ID),
                        'birthday': 'invalid'
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': 'test name',
                        'cdi_type': 'standard',
                        'parent_email': 'test email',
                        'database_id': str(TEST_DB_ID)
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_presentation_model'].side_effect = [
                TEST_PRESENTATION_FORMAT_METADATA,
                None,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA,
                TEST_PRESENTATION_FORMAT_METADATA
            ]
            mocks['load_cdi_model'].side_effect = [
                None,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT,
                TEST_FORMAT
            ]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_presentation_model'].assert_any_call('standard')
            mocks['load_presentation_model'].assert_any_call('invalid_format')
            mocks['load_cdi_model'].assert_any_call('invalid_format')
            mocks['load_cdi_model'].assert_any_call('standard')

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_forms_defaults(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': TEST_CHILD_NAME,
                        'cdi_type': 'standard',
                        'parent_email': TEST_PARENT_EMAIL,
                        'database_id': TEST_DB_ID
                    })
                )
                self.assertFalse('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_presentation_model'].return_value = TEST_PRESENTATION_FORMAT_METADATA
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_presentation_model'].assert_called_with('standard')
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_parent_form'].assert_called_with(EXPECTED_PARENT_FORM)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_forms_fila_part_way(self):
        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': ','.join(['name1','name2']),
                        'cdi_type': 'standard,standard',
                        'parent_email': ','.join([TEST_PARENT_EMAIL, 'fail']),
                        'database_id': ','.join(
                            [str(TEST_DB_ID), str(TEST_DB_ID_MOD)]
                        )
                    })
                )
                self.assertTrue('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID
            mocks['load_presentation_model'].return_value = TEST_PRESENTATION_FORMAT_METADATA
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_presentation_model'].assert_called_with('standard')
            mocks['load_cdi_model'].assert_called_with('standard')
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['generate_unique_cdi_form_id'].assert_called()

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_send_parent_forms_non_defaults(self):
        def body():
            with self.app.test_client() as client:

                resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_name': TEST_CHILD_NAME_MOD,
                        'cdi_type': 'standard_mod',
                        'parent_email': TEST_PARENT_EMAIL_MOD,
                        'study': TEST_STUDY_MOD,
                        'study_id': TEST_STUDY_ID_MOD,
                        'gender': 'female',
                        'birthday': TEST_BIRTHDAY_MOD_ISO,
                        'items_excluded': TEST_ITEMS_EXCLUDED_MOD,
                        'extra_categories': TEST_EXTRA_CATEGORIES_MOD,
                        'languages': 'english',
                        'hard_of_hearing': 'true',
                        'format': 'standard_mod'
                    })
                )
                self.assertFalse('error' in json.loads(resp.data))

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['generate_unique_cdi_form_id'].return_value = TEST_PARENT_FORM_ID_MOD
            mocks['load_presentation_model'].return_value = TEST_PRESENTATION_FORMAT_METADATA
            mocks['load_cdi_model'].return_value = TEST_FORMAT
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['generate_unique_cdi_form_id'].assert_called()
            mocks['load_presentation_model'].assert_called_with('standard_mod')
            mocks['load_cdi_model'].assert_called_with('standard_mod')
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots'
            )
            mocks['insert_parent_form'].assert_called_with(
                EXPECTED_MODIFIED_PARENT_FORM
            )

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_get_child_words_by_api(self):
        def body():
            with self.app.test_client() as client:

                resp = client.get('/base/api/v0/get_child_words.json?' +
                    urllib.parse.urlencode({
                        'api_key': TEST_API_KEY,
                        'child_id': 123
                    })
                )

                resp_info = json.loads(resp.data)
                self.assertFalse('error' in resp_info)

                word_vals = resp_info['words']
                self.assertEqual(word_vals['word1'], None)
                self.assertEqual(word_vals['word2'], '2015/01/02')

        def on_start(mocks):
            mocks['get_api_key'].return_value = TEST_API_KEY_ENTRY
            mocks['get_user'].return_value = TEST_USER
            mocks['run_search_query'].return_value = [TEST_SNAPSHOT]
            mocks['summarize_snapshots'].return_value = {'word1': None, 'word2': '2015/01/02'}

        def on_end(mocks):
            mocks['get_api_key'].assert_called_with(TEST_API_KEY)
            mocks['get_user'].assert_called_with(TEST_EMAIL)
            mocks['run_search_query'].assert_called_with(
                unittest.mock.ANY,
                'snapshots',
                True
            )
            mocks['summarize_snapshots'].assert_called_with([TEST_SNAPSHOT])

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()
