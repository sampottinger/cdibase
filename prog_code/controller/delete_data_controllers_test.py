"""Automated tests for logic used in deleting or hiding prior lab data.

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
import unittest.mock

import flask

import cdibase
from ..controller import delete_data_controllers
from ..struct import models
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import report_util
from ..util import session_util
from ..util import user_util

TEST_EMAIL = 'test_mail'
TEST_USER = models.User(
    0,
    TEST_EMAIL,
    None,
    False,
    True,
    False,
    False,
    False,
    False,
    False,
    False
)
ERROR_ATTR = constants.ERROR_ATTR
DELETE_OPERATION = delete_data_controllers.DELETE_OPERATION
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR
PASSWORD_ATTR = delete_data_controllers.PASSWORD_ATTR
OPERATION_ATTR = delete_data_controllers.OPERATION_ATTR
DELETE_WAITING_ATTR = delete_data_controllers.DELETE_WAITING_ATTR
SNAPSHOTS_DB_TABLE = constants.SNAPSHOTS_DB_TABLE

DELETE_OPERATION = delete_data_controllers.DELETE_OPERATION


class TestDeleteDataControllers(unittest.TestCase):

    def setUp(self):
        self.app = cdibase.app
        self.app.debug = True
        self.__callback_called = False

    def __run_with_mocks(self, callback, user_password_response, assert_call):
        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
            with unittest.mock.patch('prog_code.util.user_util.check_user_password') as mock_check_user_password:
                mock_get_user.return_value = TEST_USER
                mock_check_user_password.return_value = user_password_response

                callback()

                if assert_call:
                    mock_get_user.assert_called_with(TEST_EMAIL)
                    mock_check_user_password.assert_called_with(TEST_EMAIL, '1234')

                self.__callback_called = True

    def __assert_callback(self):
        self.assertTrue(self.__callback_called)

    def test_execute_delete_request(self):
        def callback():
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.post(
                    '/base/delete_data/delete_mcdi_results',
                    data={
                        PASSWORD_ATTR: '1234',
                        OPERATION_ATTR: DELETE_OPERATION
                    }
                )

                self.assertTrue(session_util.is_waiting_on_delete())

        self.__run_with_mocks(callback, True, True)
        self.__assert_callback()

    def test_execute_bad_password(self):
        def callback():
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.post(
                    '/base/delete_data/delete_mcdi_results',
                    data={
                        PASSWORD_ATTR: '1234',
                        OPERATION_ATTR: DELETE_OPERATION
                    }
                )

                self.assertFalse(session_util.is_waiting_on_delete())

        self.__run_with_mocks(callback, False, True)
        self.__assert_callback()

    def test_execute_bad_operation(self):
        def callback():
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.post(
                    '/base/delete_data/delete_mcdi_results',
                    data={
                        PASSWORD_ATTR: '1234',
                        OPERATION_ATTR: 'bad'
                    }
                )

                self.assertFalse(session_util.is_waiting_on_delete())

        self.__run_with_mocks(callback, True, True)
        self.__assert_callback()

    def test_is_waiting_on_download(self):
        def callback():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL
                    session_util.set_waiting_on_delete(False, sess)

                resp = client.get('/base/delete_data/is_waiting')
                self.assertFalse(json.loads(resp.data)[DELETE_WAITING_ATTR])

                with client.session_transaction() as sess:
                    session_util.set_waiting_on_delete(True, sess)
                resp = client.get('/base/delete_data/is_waiting')
                self.assertTrue(json.loads(resp.data)[DELETE_WAITING_ATTR])

                with client.session_transaction() as sess:
                    session_util.set_waiting_on_delete(False, sess)
                resp = client.get('/base/delete_data/is_waiting')
                self.assertFalse(json.loads(resp.data)[DELETE_WAITING_ATTR])

        self.__run_with_mocks(callback, True, False)
        self.__assert_callback()

    def test_incomplete_add_filter(self):
        def callback():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.post('/base/delete_data/add_filter')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertTrue('not specified' in sess[ERROR_ATTR].lower())
                    sess[ERROR_ATTR] = ''

                resp = client.post('/base/delete_data/add_filter', data={
                    'field': 'val1'
                })
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertTrue('not specified' in sess[ERROR_ATTR].lower())
                    sess[ERROR_ATTR] = ''

                resp = client.post('/base/delete_data/add_filter', data={
                    'field': 'val1',
                    'operator': 'val2',
                })
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertTrue('not specified' in sess[ERROR_ATTR].lower())
                    sess[ERROR_ATTR] = ''

                resp = client.post('/base/delete_data/add_filter', data={
                    'operand': 'val3',
                    'operator': 'val2',
                })
                self.assertEqual(resp.status_code, 302)

        self.__run_with_mocks(callback, True, False)
        self.__assert_callback()

    def test_add_filter(self):
        def callback():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.post('/base/delete_data/add_filter', data={
                    'field': 'val1',
                    'operator': 'val2',
                    'operand': 'val3'
                })
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertFalse(ERROR_ATTR in sess)

                    filters = session_util.get_filters(sess)
                    self.assertEqual(len(filters), 1)
                    target_filter = filters[0]
                    self.assertEqual(target_filter.field, 'val1')
                    self.assertEqual(target_filter.operator, 'val2')
                    self.assertEqual(target_filter.operand, 'val3')

        self.__run_with_mocks(callback, True, False)
        self.__assert_callback()

    def test_remove_filter(self):
        def callback():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL
                    session_util.add_filter(
                        models.Filter('val1', 'val2', 'val3'),
                        sess
                    )
                    session_util.add_filter(
                        models.Filter('val4', 'val5', 'val6'),
                        sess
                    )

                resp = client.get('/base/delete_data/delete_filter/0')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    filters = session_util.get_filters(sess)
                    self.assertEqual(len(filters), 1)
                    self.assertEqual(filters[0].field, 'val4')
                    self.assertFalse(ERROR_ATTR in sess)

                resp = client.get('/base/delete_data/delete_filter/0')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    filters = session_util.get_filters(sess)
                    self.assertEqual(len(filters), 0)
                    self.assertFalse(ERROR_ATTR in sess)

                resp = client.get('/base/delete_data/delete_filter/0')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    filters = session_util.get_filters(sess)
                    self.assertEqual(len(filters), 0)
                    self.assertTrue('already deleted' in sess[ERROR_ATTR])

        self.__run_with_mocks(callback, True, False)
        self.__assert_callback()

    def test_access_requests(self):
        TEST_PAYLOAD = '{"restore": true, "filters": [{"operand": "val3", "field": "val1", "operator": "val2", "operand_float": null}, {"operand": "val6", "field": "val4", "operator": "val5", "operand_float": null}]}'

        query_results = [models.SnapshotMetadata(
            'database_id',
            'child_id',
            'study_id',
            'study',
            'gender',
            'age',
            'birthday',
            'session_date',
            'session_num',
            'total_num_sessions',
            'words_spoken',
            'items_excluded',
            'percentile',
            'extra_categories',
            'revision',
            'languages',
            'num_languages',
            'mcdi_type',
            'hard_of_hearing',
            False
        )]

        def body():
            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL
                    sess['format'] = 'test_format'

                    session_util.add_filter(
                        models.Filter('val1', 'val2', 'val3'),
                        sess
                    )
                    session_util.add_filter(
                        models.Filter('val4', 'val5', 'val6'),
                        sess
                    )

                    session_util.set_waiting_on_delete(True, sess)

                client.get('/base/delete_data/execute')

        with unittest.mock.patch('prog_code.util.db_util.report_usage') as mock_report_usage:
            with unittest.mock.patch('prog_code.util.filter_util.run_delete_query') as mock_run_delete_query:
                with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:

                    mock_get_user.return_value = TEST_USER

                    body()

                    mock_get_user.assert_called_with(TEST_EMAIL)
                    mock_report_usage.assert_called_with(
                        TEST_EMAIL,
                        "Delete Data",
                        unittest.mock.ANY
                    )
                    mock_run_delete_query.assert_called_with(
                        unittest.mock.ANY,
                        SNAPSHOTS_DB_TABLE,
                        True
                    )
