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

import flask
import mox

import daxlabbase
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


class TestDeleteDataControllers(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.app = daxlabbase.app
        self.app.debug = True

    def test_execute_delete_request(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'check_user_password')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.check_user_password(TEST_EMAIL, '1234').AndReturn(True)
        self.mox.ReplayAll()

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

    def test_execute_bad_password(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'check_user_password')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.check_user_password(TEST_EMAIL, '1234').AndReturn(False)
        self.mox.ReplayAll()

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

    def test_execute_bad_operation(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(user_util, 'check_user_password')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.check_user_password(TEST_EMAIL, '1234').AndReturn(False)
        self.mox.ReplayAll()

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

    def test_is_waiting_on_download(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

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

    def test_incomplete_add_filter(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

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

    def test_add_filter(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

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

    def test_remove_filter(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

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

        self.mox.StubOutWithMock(db_util, 'report_usage')
        self.mox.StubOutWithMock(filter_util, 'run_delete_query')
        self.mox.StubOutWithMock(user_util, 'get_user')
        
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.report_usage(
            TEST_EMAIL,
            "Delete Data",
            TEST_PAYLOAD
        )

        filter_util.run_delete_query(
            mox.IsA(list),
            SNAPSHOTS_DB_TABLE,
            True
        ).AndReturn

        self.mox.ReplayAll()

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
