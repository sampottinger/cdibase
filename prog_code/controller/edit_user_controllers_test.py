import mox

import daxlabbase
from ..struct import models
from ..util import constants
from ..util import db_util
from ..util import user_util

TEST_EMAIL = 'test.email@example.com'
TARGET_EMAIL = 'target.user@example.com'
TEST_DB_ID = 1
TARGET_DB_ID = 2
TEST_USER = models.User(
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
    True
)
TARGET_USER = models.User(
    TARGET_DB_ID,
    TARGET_EMAIL,
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
NEW_EMAIL = 'new_email@example.com'


class TestEditParentControllers(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.app = daxlabbase.app
        self.app.debug = True

    def test_delete_user(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'delete_user')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TARGET_EMAIL).AndReturn(TARGET_USER)
        user_util.delete_user(TARGET_EMAIL)
       
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TARGET_EMAIL).AndReturn(None)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            url = '/base/edit_users/%s/delete' % TARGET_EMAIL
            client.get(url)

            with client.session_transaction() as sess:
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)
                del sess[constants.CONFIRMATION_ATTR]
                self.assertFalse(constants.ERROR_ATTR in sess)

            url = '/base/edit_users/%s/delete' % TARGET_EMAIL
            client.get(url)

            with client.session_transaction() as sess:
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)
                self.assertTrue(constants.ERROR_ATTR in sess)

    def test_edit_user(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'delete_user')
        self.mox.StubOutWithMock(user_util, 'update_user')
        
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TARGET_EMAIL).AndReturn(None)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TARGET_EMAIL).AndReturn(TARGET_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TARGET_EMAIL).AndReturn(TARGET_USER)
        user_util.get_user(NEW_EMAIL).AndReturn(None)
        user_util.update_user(
            TARGET_EMAIL,
            NEW_EMAIL,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False
        )

        self.mox.ReplayAll()

        with self.app.test_client() as client:

            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            url = '/base/edit_users/%s/edit' % TARGET_EMAIL
            client.post(url)
            with client.session_transaction() as sess:
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)
                self.assertTrue(constants.ERROR_ATTR in sess)
                del sess[constants.ERROR_ATTR]

            url = '/base/edit_users/%s/edit' % TARGET_EMAIL
            client.post(url, data={
                'new_email': TEST_EMAIL
            })
            with client.session_transaction() as sess:
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)
                self.assertTrue(constants.ERROR_ATTR in sess)
                del sess[constants.ERROR_ATTR]

            url = '/base/edit_users/%s/edit' % TARGET_EMAIL
            client.post(url, data={
                'new_email': NEW_EMAIL,
                'can_enter_data': constants.FORM_SELECTED_VALUE,
                'can_import_data': constants.FORM_SELECTED_VALUE,
                'can_access_data': constants.FORM_SELECTED_VALUE,
                'can_use_api_key': constants.FORM_SELECTED_VALUE
            })
            with client.session_transaction() as sess:
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)
                self.assertFalse(constants.ERROR_ATTR in sess)

    def test_add_user(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'create_new_user')
        
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TARGET_EMAIL).AndReturn(TARGET_USER)
        
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(NEW_EMAIL).AndReturn(None)
        user_util.create_new_user(
            NEW_EMAIL,
            True,
            False,
            True,
            False,
            True,
            False,
            True,
            False
        )

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            client.post('/base/edit_users/_add', data={
                'new_email': '',
                'can_enter_data': constants.FORM_SELECTED_VALUE,
                'can_import_data': constants.FORM_SELECTED_VALUE,
                'can_access_data': constants.FORM_SELECTED_VALUE,
                'can_use_api_key': constants.FORM_SELECTED_VALUE
            })
            with client.session_transaction() as sess:
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)
                self.assertTrue(constants.ERROR_ATTR in sess)
                del sess[constants.ERROR_ATTR]

            client.post('/base/edit_users/_add', data={
                'new_email': TARGET_EMAIL,
                'can_enter_data': constants.FORM_SELECTED_VALUE,
                'can_import_data': constants.FORM_SELECTED_VALUE,
                'can_access_data': constants.FORM_SELECTED_VALUE,
                'can_use_api_key': constants.FORM_SELECTED_VALUE
            })
            with client.session_transaction() as sess:
                self.assertFalse(constants.CONFIRMATION_ATTR in sess)
                self.assertTrue(constants.ERROR_ATTR in sess)
                del sess[constants.ERROR_ATTR]

            client.post('/base/edit_users/_add', data={
                'new_email': NEW_EMAIL,
                'can_enter_data': constants.FORM_SELECTED_VALUE,
                'can_import_data': constants.FORM_SELECTED_VALUE,
                'can_access_data': constants.FORM_SELECTED_VALUE,
                'can_use_api_key': constants.FORM_SELECTED_VALUE
            })
            with client.session_transaction() as sess:
                self.assertTrue(constants.CONFIRMATION_ATTR in sess)
                self.assertFalse(constants.ERROR_ATTR in sess)
