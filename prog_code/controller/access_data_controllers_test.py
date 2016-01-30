"""Automated tsts for logic used to access prior lab data.

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
from ..controller import access_data_controllers
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
    False,
    False,
    False,
    True,
    False,
    False,
    False
)
ERROR_ATTR = constants.ERROR_ATTR
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR


class TestZipFile:
    def getvalue(self):
        return 'test zip file contents'


class TestCSVFile:
    def getvalue(self):
        return 'test CSV file contents'


class TestAccessDataControllers(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.app = daxlabbase.app
        self.app.debug = True

    def test_execute_access_request(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

        expected_url_archive = '/access_data/download_mcdi_results.zip'

        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            resp = client.post('/base/access_data/download_mcdi_results')

            self.assertTrue(session_util.is_waiting_on_download())

    def test_execute_access_request_consolidated(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

        expected_url_combined = '/access_data/download_mcdi_results.csv'

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            attr_name = 'consolidated_csv'
            attr_value = access_data_controllers.HTML_CHECKBOX_SELECTED
            url = '/base/access_data/download_mcdi_results?%s=%s' % (
                attr_name, attr_value)
            resp = client.post(url)

            self.assertEqual(
                flask.session[access_data_controllers.FORMAT_SESSION_ATTR],
                ''
            )

            self.assertTrue(session_util.is_waiting_on_download())

    def test_execute_access_request_format(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

        expected_url_combined = '/access_data/download_mcdi_results.csv'

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL

            cons_name = 'consolidated_csv'
            cons_value = access_data_controllers.HTML_CHECKBOX_SELECTED
            fmt_name = access_data_controllers.FORMAT_SESSION_ATTR
            fmt_value = 'testFormat'
            url = '/base/access_data/download_mcdi_results?'
            resp = client.post(url, data={
                cons_name: cons_value,
                fmt_name: fmt_value
            })

            self.assertEqual(
                flask.session[access_data_controllers.FORMAT_SESSION_ATTR],
                'testFormat'
            )

            self.assertTrue(session_util.is_waiting_on_download())

    def test_is_waiting_on_download(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL
                session_util.set_waiting_on_download(False, sess)

            resp = client.get('/base/access_data/is_waiting')
            self.assertFalse(json.loads(resp.data)['is_waiting'])

            with client.session_transaction() as sess:
                session_util.set_waiting_on_download(True, sess)
            resp = client.get('/base/access_data/is_waiting')
            self.assertTrue(json.loads(resp.data)['is_waiting'])

            with client.session_transaction() as sess:
                session_util.set_waiting_on_download(False, sess)
            resp = client.get('/base/access_data/is_waiting')
            self.assertFalse(json.loads(resp.data)['is_waiting'])

    def test_abort_download(self):
        self.mox.StubOutWithMock(user_util, 'get_user')
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        self.mox.ReplayAll()

        with self.app.test_client() as client:
            
            with client.session_transaction() as sess:
                sess['email'] = TEST_EMAIL
                session_util.set_waiting_on_download(True, sess)

            resp = client.get('/base/access_data/is_waiting')
            self.assertTrue(json.loads(resp.data)['is_waiting'])
            client.get('/base/access_data/abort')

            with client.session_transaction() as sess:
                session_util.set_waiting_on_download(False, sess)

            resp = client.get('/base/access_data/is_waiting')
            self.assertFalse(json.loads(resp.data)['is_waiting'])
            client.get('/base/access_data/abort')
            
            resp = client.get('/base/access_data/is_waiting')
            self.assertFalse(json.loads(resp.data)['is_waiting'])

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

            resp = client.post('/base/access_data/add_filter')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                self.assertTrue('not specified' in sess[ERROR_ATTR].lower())
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/access_data/add_filter', data={
                'field': 'val1'
            })
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                self.assertTrue('not specified' in sess[ERROR_ATTR].lower())
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/access_data/add_filter', data={
                'field': 'val1',
                'operator': 'val2',
            })
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                self.assertTrue('not specified' in sess[ERROR_ATTR].lower())
                sess[ERROR_ATTR] = ''

            resp = client.post('/base/access_data/add_filter', data={
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

            resp = client.post('/base/access_data/add_filter', data={
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

            resp = client.get('/base/access_data/delete_filter/0')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                filters = session_util.get_filters(sess)
                self.assertEqual(len(filters), 1)
                self.assertEqual(filters[0].field, 'val4')
                self.assertFalse(ERROR_ATTR in sess)

            resp = client.get('/base/access_data/delete_filter/0')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                filters = session_util.get_filters(sess)
                self.assertEqual(len(filters), 0)
                self.assertFalse(ERROR_ATTR in sess)

            resp = client.get('/base/access_data/delete_filter/0')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                filters = session_util.get_filters(sess)
                self.assertEqual(len(filters), 0)
                self.assertTrue('already deleted' in sess[ERROR_ATTR])

    def test_access_requests(self):
        TEST_USAGE_REPORT_PAYLOAD = '{"include deleted": true, "filters": [{"operand": "val3", "field": "val1", "operator": "val2", "operand_float": null}, {"operand": "val6", "field": "val4", "operator": "val5", "operand_float": null}]}'

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
        test_zip_file = TestZipFile()
        test_csv_file = TestCSVFile()

        self.mox.StubOutWithMock(user_util, 'get_user')
        self.mox.StubOutWithMock(filter_util, 'run_search_query')
        self.mox.StubOutWithMock(db_util, 'load_presentation_model')
        self.mox.StubOutWithMock(db_util, 'report_usage')
        self.mox.StubOutWithMock(report_util, 'generate_study_report')
        self.mox.StubOutWithMock(report_util,
            'generate_consolidated_study_report')

        # First request
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.report_usage(
            'test_mail',
            'Download Data as zip',
            TEST_USAGE_REPORT_PAYLOAD
        )

        filter_util.run_search_query(mox.IsA(list), 'snapshots',
            True).AndReturn(query_results)
        db_util.load_presentation_model('test_format').AndReturn(
            'test_format_spec')
        report_util.generate_study_report(query_results,
            'test_format_spec').AndReturn(test_zip_file)

        # Second request
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)

        db_util.report_usage(
            'test_mail',
            'Download Data as zip',
            TEST_USAGE_REPORT_PAYLOAD
        )

        filter_util.run_search_query(mox.IsA(list), 'snapshots',
            True).AndReturn(query_results)
        db_util.load_presentation_model('test_format_2').AndReturn(None)

        # Third request
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        
        db_util.report_usage(
            'test_mail',
            'Download Data as CSV',
            TEST_USAGE_REPORT_PAYLOAD
        )

        filter_util.run_search_query(mox.IsA(list), 'snapshots',
            True).AndReturn(query_results)
        db_util.load_presentation_model('test_format').AndReturn(
            'test_format_spec')
        report_util.generate_consolidated_study_report(query_results,
            'test_format_spec').AndReturn(test_csv_file)

        # Final request
        user_util.get_user(TEST_EMAIL).AndReturn(TEST_USER)
        
        db_util.report_usage(
            'test_mail',
            'Download Data as zip',
            TEST_USAGE_REPORT_PAYLOAD
        )

        filter_util.run_search_query(mox.IsA(list), 'snapshots',
            True).AndReturn(query_results)
        db_util.load_presentation_model('test_format_2').AndReturn(None)

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

                session_util.set_waiting_on_download(True, sess)

            resp = client.get('/base/access_data/download_mcdi_results.zip')
            self.assertEqual(
                resp.headers['Content-Type'],
                access_data_controllers.OCTET_MIME_TYPE
            )
            self.assertEqual(
                resp.headers['Content-Disposition'],
                access_data_controllers.CONTENT_DISPOISTION_ZIP
            )
            self.assertEqual(
                resp.headers['Content-Length'],
                str(len(test_zip_file.getvalue()))
            )
            self.assertEqual(
                resp.mimetype,
                access_data_controllers.OCTET_MIME_TYPE
            )
            self.assertEqual(
                resp.data,
                test_zip_file.getvalue()
            )

            with client.session_transaction() as sess:
                self.assertFalse(session_util.is_waiting_on_download(sess))
                session_util.set_waiting_on_download(True, sess)

            with client.session_transaction() as sess:
                sess['format'] = 'test_format_2'

            resp = client.get('/base/access_data/download_mcdi_results.zip')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                self.assertTrue('presentation format' in sess[ERROR_ATTR])
                self.assertFalse(session_util.is_waiting_on_download(sess))
                sess['format'] = 'test_format'
                session_util.set_waiting_on_download(True, sess)

            resp = client.get('/base/access_data/download_mcdi_results.csv')
            self.assertEqual(
                resp.headers['Content-Type'],
                access_data_controllers.CSV_MIME_TYPE
            )
            self.assertEqual(
                resp.headers['Content-Disposition'],
                access_data_controllers.CONTENT_DISPOISTION_CSV
            )
            self.assertEqual(
                resp.headers['Content-Length'],
                str(len(test_csv_file.getvalue()))
            )
            self.assertEqual(
                resp.mimetype,
                access_data_controllers.CSV_MIME_TYPE
            )
            self.assertEqual(
                resp.data,
                test_csv_file.getvalue()
            )

            with client.session_transaction() as sess:
                self.assertFalse(session_util.is_waiting_on_download(sess))
                session_util.set_waiting_on_download(True, sess)

            with client.session_transaction() as sess:
                sess['format'] = 'test_format_2'

            resp = client.get('/base/access_data/download_mcdi_results.zip')
            self.assertEqual(resp.status_code, 302)

            with client.session_transaction() as sess:
                self.assertTrue('presentation format' in sess[ERROR_ATTR])
                self.assertFalse(session_util.is_waiting_on_download(sess))
