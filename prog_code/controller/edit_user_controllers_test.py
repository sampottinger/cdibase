
"""Automated tests for editing user accounts.

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
import unittest

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


class TestEditUserControllers(unittest.TestCase):

    def setUp(self):
        self.app = daxlabbase.app
        self.app.debug = True
        self.__callback_called = False

    def __run_with_mocks(self, on_start, body, on_end):
        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.user_util.delete_user') as mock_delete_user:
                with unittest.mock.patch('prog_code.util.user_util.update_user') as mock_update_user:
                    with unittest.mock.patch('prog_code.util.user_util.create_new_user') as mock_create_new_user:
                        with unittest.mock.patch('prog_code.util.db_util.report_usage') as mock_report_usage:

                            mocks = {
                                'get_user': mock_get_user,
                                'delete_user': mock_delete_user,
                                'update_user': mock_update_user,
                                'create_new_user': mock_create_new_user,
                                'report_usage': mock_report_usage
                            }

                            on_start(mocks)
                            body()
                            on_end(mocks)

                            self.__callback_called = True

    def __assert_callback(self):
        self.assertTrue(self.__callback_called)

    def test_delete_user(self):
        def body():
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

        def on_start(mocks):
            mocks['get_user'].side_effect = [
                TEST_USER,
                TARGET_USER,
                TEST_USER,
                None
            ]

        def on_end(mocks):
            mocks['get_user'].assert_any_call(TEST_EMAIL)
            mocks['get_user'].assert_any_call(TARGET_EMAIL)
            mocks['report_usage'].assert_called_once()
            mocks['report_usage'].assert_called_with(
                TEST_EMAIL,
                'Delete User',
                json.dumps({'user': TARGET_EMAIL})
            )
            mocks['delete_user'].assert_called_once()
            mocks['delete_user'].assert_called_with(TARGET_EMAIL)

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_edit_user(self):
        def body():
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

        def on_start(mocks):
            mocks['get_user'].side_effect = [
                TEST_USER,
                None,
                TEST_USER,
                TARGET_USER,
                TEST_USER,
                TEST_USER,
                TARGET_USER,
                None
            ]

        def on_end(mocks):
            mocks['get_user'].assert_any_call(TEST_EMAIL)
            mocks['get_user'].assert_any_call(TARGET_EMAIL)
            mocks['report_usage'].assert_called_with(
                TEST_EMAIL,
                'Edit User',
                json.dumps({'user': TARGET_EMAIL})
            )
            mocks['update_user'].assert_called_with(
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

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()

    def test_add_user(self):
        def body():
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

        def on_start(mocks):
            mocks['get_user'].side_effect = [
                TEST_USER,
                TEST_USER,
                TARGET_USER,
                TEST_USER,
                None
            ]

        def on_end(mocks):
            mocks['get_user'].assert_any_call(TEST_EMAIL)
            mocks['get_user'].assert_any_call(TARGET_EMAIL)
            mocks['get_user'].assert_any_call(NEW_EMAIL)

            mocks['report_usage'].assert_called_once()
            mocks['report_usage'].assert_called_with(
                TEST_EMAIL,
                "Add User",
                json.dumps({"user": NEW_EMAIL})
            )

            mocks['create_new_user'].assert_called_once()
            mocks['create_new_user'].assert_called_with(
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

        self.__run_with_mocks(on_start, body, on_end)
        self.__assert_callback()
