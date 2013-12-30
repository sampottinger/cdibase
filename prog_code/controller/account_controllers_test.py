import mox

import daxlabbase
from ..struct import models
from ..util import constants
from ..util import user_util

ERROR_ATTR = constants.ERROR_ATTR
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR
TEST_EMAIL = 'test_mail'
TEST_USER = models.User(
    0,
    TEST_EMAIL,
    None,
    False,
    False,
    False,
    True,
    False,
    False,
    False,
    False
)


class TestAccountControllers(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.app = daxlabbase.app

    def test_login(self):
        self.mox.StubOutWithMock(user_util, 'check_user_password')
        user_util.check_user_password('', '').AndReturn(False)
        user_util.check_user_password(TEST_EMAIL, '').AndReturn(False)
        user_util.check_user_password(TEST_EMAIL, 'incorrect').AndReturn(False)
        user_util.check_user_password(TEST_EMAIL, 'correct').AndReturn(True)
        self.mox.ReplayAll()

        with self.app.test_client() as client:
            resp = client.post('/base/account/login')

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/login', data={
                'email': TEST_EMAIL
            })

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/login', data={
                'email': TEST_EMAIL,
                'password': 'incorrect'
            })

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/login', data={
                'email': TEST_EMAIL,
                'password': 'correct'
            })

            with client.session_transaction() as sess:
                self.assertEqual(sess[ERROR_ATTR], '')
                self.assertNotEqual(sess[CONFIRMATION_ATTR], '')

    def test_forgot_password(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'reset_password')

        user_util.get_user('fake_user').AndReturn(False)
        user_util.get_user(TEST_EMAIL).AndReturn(True)
        user_util.reset_password(TEST_EMAIL)
        self.mox.ReplayAll()

        with self.app.test_client() as client:
            resp = client.post('/base/account/forgot_password')

            with client.session_transaction() as sess:
                self.assertFalse(ERROR_ATTR in sess)
                self.assertTrue(CONFIRMATION_ATTR in sess)

            resp = client.post('/base/account/forgot_password', data={
                'email': 'fake_user'
            })

            with client.session_transaction() as sess:
                self.assertFalse(ERROR_ATTR in sess)
                self.assertTrue(CONFIRMATION_ATTR in sess)

            resp = client.post('/base/account/forgot_password', data={
                'email': TEST_EMAIL
            })

            with client.session_transaction() as sess:
                self.assertFalse(ERROR_ATTR in sess)
                self.assertTrue(CONFIRMATION_ATTR in sess)

    def test_logout(self):
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            client.get('/base/account/logout')

            with client.session_transaction() as sess:
                self.assertFalse(ERROR_ATTR in sess)
                self.assertTrue(CONFIRMATION_ATTR in sess)
                self.assertFalse('email' in sess)

    def test_change_password_fail(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'check_user_password')
        self.mox.StubOutWithMock(user_util, 'change_user_password')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.check_user_password(TEST_EMAIL, 'wrong password').AndReturn(
            False)

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.post('/base/account/change_password')

            self.assertIn('location', resp.headers)
            self.assertNotEqual(
                resp.headers['location'].find('change_password'),
                -1
            )

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/change_password', data={
                'current_password': 'current password'
            })

            self.assertIn('location', resp.headers)
            self.assertNotEqual(
                resp.headers['location'].find('change_password'),
                -1
            )

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/change_password', data={
                'current_password': 'current password',
                'new_password': 'new password'
            })

            self.assertIn('location', resp.headers)
            self.assertNotEqual(
                resp.headers['location'].find('change_password'),
                -1
            )

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/change_password', data={
                'current_password': 'current password',
                'new_password': '',
                'confirm_new_password': ''
            })

            self.assertIn('location', resp.headers)
            self.assertNotEqual(
                resp.headers['location'].find('change_password'),
                -1
            )

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/account/change_password', data={
                'current_password': 'wrong password',
                'new_password': 'new password',
                'confirm_new_password': 'new password'
            })

            self.assertIn('location', resp.headers)
            self.assertNotEqual(
                resp.headers['location'].find('change_password'),
                -1
            )

            with client.session_transaction() as sess:
                self.assertNotEqual(sess[ERROR_ATTR], '')
                sess[ERROR_ATTR] = ''

    def test_change_password(self):
        self.mox.StubOutWithMock(user_util, 'get_user')

        self.mox.StubOutWithMock(user_util, 'check_user_password')
        self.mox.StubOutWithMock(user_util, 'change_user_password')

        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.check_user_password(TEST_EMAIL,
            'current password').AndReturn(True)
        user_util.change_user_password(TEST_EMAIL, 'new password')

        self.mox.ReplayAll()

        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.post('/base/account/change_password', data={
                'current_password': 'current password',
                'new_password': 'new password',
                'confirm_new_password': 'new password'
            })

            self.assertIn('location', resp.headers)
            self.assertEqual(
                resp.headers['location'].find('change_password'),
                -1
            )

            with client.session_transaction() as sess:
                self.assertFalse(ERROR_ATTR in sess)
                self.assertNotEqual(sess[CONFIRMATION_ATTR], '')
