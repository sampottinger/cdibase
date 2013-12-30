import json
import math
import urllib

import mox

import daxlabbase
from ..controller import api_key_controllers
from ..struct import models
from ..util import api_key_util
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import parent_account_util
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
    TEST_HARD_OF_HEARING,
    False
)
TEST_FORMAT = models.MCDIFormat(
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
    constants.EXPLICIT_FALSE
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
    constants.EXPLICIT_TRUE
)


class TestAPIKeyControllers(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.app = daxlabbase.app
        self.app.debug = True

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
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(session_util, 'get_user_id')
        self.mox.StubOutWithMock(api_key_util, 'create_new_api_key')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        session_util.get_user_id().AndReturn(TEST_DB_ID)
        api_key_util.create_new_api_key(TEST_DB_ID)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/config_api_key/new')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[constants.CONFIRMATION_ATTR], '')
                self.assertFalse(constants.ERROR_ATTR in sess)

    def test_verify_api_key_for_parent_forms(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')

        db_util.get_api_key(TEST_API_KEY).AndReturn(None)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(models.User(
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
        ))

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(models.User(
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
        ))

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        self.mox.ReplayAll()

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

    def test_send_parent_form_missing_params(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_form')
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                    urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': 'test parent'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

    def test_send_parent_form_invalid_params(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('invalid_format').AndReturn(None)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('invalid_format').AndReturn(None)
        db_util.load_mcdi_model('standard').AndReturn(None)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'invalid_format',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': TEST_DB_ID
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'format': 'invalid_format',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': TEST_DB_ID
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': 'invalid type'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': 'test',
                    'database_id': TEST_DB_ID
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': str(TEST_DB_ID),
                    'gender': 'invalid'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': str(TEST_DB_ID),
                    'hard_of_hearing': 'invalid'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': str(TEST_DB_ID),
                    'birthday': 'invalid'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': 'test email',
                    'database_id': str(TEST_DB_ID)
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

    def test_send_parent_form_defaults(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_PARENT_FORM)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': TEST_CHILD_NAME,
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': TEST_DB_ID
                })
            )
            self.assertFalse('error' in json.loads(resp.data))

    def test_send_parent_form_non_defaults(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID_MOD)
        db_util.load_presentation_model('standard_mod').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard_mod').AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_MODIFIED_PARENT_FORM)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': TEST_CHILD_NAME_MOD,
                    'mcdi_type': 'standard_mod',
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

    def test_send_parent_forms_missing_params(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_forms')
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_form?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                    urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': 'test parent'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

    def test_send_parent_forms_invalid_params(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('invalid_format').AndReturn(None)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        db_util.load_presentation_model('invalid_format').AndReturn(None)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'invalid_format',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': TEST_DB_ID
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'format': 'invalid_format',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': TEST_DB_ID
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': 'invalid type'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': 'test wrong email',
                    'database_id': str(TEST_DB_ID)
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': str(TEST_DB_ID),
                    'gender': 'invalid'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': str(TEST_DB_ID),
                    'hard_of_hearing': 'invalid'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': str(TEST_DB_ID),
                    'birthday': 'invalid'
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': 'test name',
                    'mcdi_type': 'standard',
                    'parent_email': 'test email',
                    'database_id': str(TEST_DB_ID)
                })
            )
            self.assertTrue('error' in json.loads(resp.data))

    def test_send_parent_forms_defaults(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_PARENT_FORM)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': TEST_CHILD_NAME,
                    'mcdi_type': 'standard',
                    'parent_email': TEST_PARENT_EMAIL,
                    'database_id': TEST_DB_ID
                })
            )
            self.assertFalse('error' in json.loads(resp.data))

    def test_send_parent_forms_fila_part_way(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_presentation_model('standard').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])

        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID)
        db_util.load_mcdi_model('standard').AndReturn(TEST_FORMAT)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': ','.join(['name1','name2']),
                    'mcdi_type': 'standard,standard',
                    'parent_email': ','.join([TEST_PARENT_EMAIL, 'fail']),
                    'database_id': ','.join(
                        [str(TEST_DB_ID), str(TEST_DB_ID_MOD)]
                    )
                })
            )
            self.assertTrue('error' in json.loads(resp.data))


    def test_send_parent_forms_non_defaults(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(db_util, 'load_mcdi_model')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'insert_parent_form')
        self.mox.StubOutWithMock(parent_account_util,
            'generate_unique_mcdi_form_id')

        db_util.get_api_key(TEST_API_KEY).AndReturn(TEST_API_KEY_ENTRY)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        parent_account_util.generate_unique_mcdi_form_id().AndReturn(
            TEST_PARENT_FORM_ID_MOD)
        db_util.load_presentation_model('standard_mod').AndReturn(
            TEST_PRESENTATION_FORMAT_METADATA)
        db_util.load_mcdi_model('standard_mod').AndReturn(TEST_FORMAT)
        filter_util.run_search_query(mox.IsA(list), 'snapshots').AndReturn(
            [TEST_SNAPSHOT])
        db_util.insert_parent_form(EXPECTED_MODIFIED_PARENT_FORM)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.get('/base/api/v0/send_parent_forms?' +
                urllib.urlencode({
                    'api_key': TEST_API_KEY,
                    'child_name': TEST_CHILD_NAME_MOD,
                    'mcdi_type': 'standard_mod',
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
