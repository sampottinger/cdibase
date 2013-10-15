import copy

import mox

import daxlabbase
from ..util import constants
from ..util import db_util
from ..util import filter_util
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
TEST_PARENT_FORM_ID_MOD = 30
TEST_CHILD_NAME_MOD = 'Test Child2'
TEST_PARENT_EMAIL_MOD = 'parent2@example.com'
TEST_DB_ID_MOD = 321
TEST_STUDY_ID_MOD = 654
TEST_STUDY_MOD = 'test study 2'
TEST_BIRTHDAY_MOD = '2011/09/13'
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
        del minimal_data_template['gender']
        del minimal_data_template['birthday']
        del minimal_data_template['items_excluded']
        del minimal_data_template['extra_categories']
        del minimal_data_template['languages']
        del minimal_data_template['hard_of_hearing']

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
