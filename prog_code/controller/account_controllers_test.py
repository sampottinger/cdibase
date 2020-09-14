"""Unit tests for logic used to edit user accounts.

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
import unittest.mock

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


class TestAccountControllers(unittest.TestCase):

    def setUp(self):
        self.app = daxlabbase.app

    def test_login(self):
        with unittest.mock.patch('prog_code.util.user_util.check_user_password') as mock:
            mock.side_effect = [False, False, False, True]

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

            self.assertEqual(len(mock.call_args_list), 4)
            self.assertEqual(mock.call_args_list[0][0][0], '')
            self.assertEqual(mock.call_args_list[0][0][1], '')
            self.assertEqual(mock.call_args_list[1][0][0], TEST_EMAIL)
            self.assertEqual(mock.call_args_list[1][0][1], '')
            self.assertEqual(mock.call_args_list[2][0][0], TEST_EMAIL)
            self.assertEqual(mock.call_args_list[2][0][1], 'incorrect')
            self.assertEqual(mock.call_args_list[3][0][0], TEST_EMAIL)
            self.assertEqual(mock.call_args_list[3][0][1], 'correct')

    def test_forgot_password(self):
        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.user_util.reset_password') as mock_reset_password:
                mock_get_user.side_effect = [False, True]

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

                self.assertEqual(len(mock_get_user.mock_calls), 2)
                mock_get_user.assert_any_call('fake_user')
                mock_get_user.assert_any_call(TEST_EMAIL)

                self.assertEqual(len(mock_reset_password.mock_calls), 1)
                mock_reset_password.assert_called_with(TEST_EMAIL)

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
        def callback():
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

        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.user_util.check_user_password') as mock_check:
                with unittest.mock.patch('prog_code.util.user_util.change_user_password') as mock_change:
                    mock_get_user.get_user.return_value = TEST_USER
                    mock_check.return_value = False

                    callback()

                    mock_get_user.assert_called_with(TEST_EMAIL)
                    mock_check.assert_called_with(TEST_EMAIL, 'wrong password')
                    self.assertEqual(len(mock_change.mock_calls), 0)

    def test_change_password(self):
        def callback():
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


        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.user_util.check_user_password') as mock_check:
                with unittest.mock.patch('prog_code.util.user_util.change_user_password') as mock_change:
                    mock_get_user.get_user.return_value = TEST_USER
                    mock_check.return_value = True

                    callback()

                    mock_get_user.assert_called_with(TEST_EMAIL)
                    mock_check.assert_called_with(TEST_EMAIL, 'current password')
                    self.assertEqual(len(mock_change.mock_calls), 1)
                    mock_change.assert_called_with(TEST_EMAIL, 'new password')
