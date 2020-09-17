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
import unittest
import unittest.mock

import flask

import cdibase
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


class TestAccessDataControllers(unittest.TestCase):

    def setUp(self):
        self.app = cdibase.app
        self.app.debug = True
        self.__callback_called = False

    def __inject_test_user(self, callback):
        with unittest.mock.patch('prog_code.util.user_util.get_user') as mock:
            mock.return_value = TEST_USER
            self.__callback_called = True
            callback()
            mock.assert_any_call(TEST_EMAIL)

    def __assert_callback_called(self):
        self.assertTrue(self.__callback_called)

    def test_execute_access_request(self):
        def callback():
            expected_url_archive = '/access_data/download_cdi_results.zip'

            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                resp = client.post('/base/access_data/download_cdi_results')

                self.assertTrue(session_util.is_waiting_on_download())

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_execute_access_request_consolidated(self):
        def callback():
            expected_url_combined = '/access_data/download_cdi_results.csv'

            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                attr_name = 'consolidated_csv'
                attr_value = access_data_controllers.HTML_CHECKBOX_SELECTED
                url = '/base/access_data/download_cdi_results?%s=%s' % (
                    attr_name, attr_value)
                resp = client.post(url)

                self.assertEqual(
                    flask.session[access_data_controllers.FORMAT_SESSION_ATTR],
                    ''
                )

                self.assertTrue(session_util.is_waiting_on_download())

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_execute_access_request_format(self):
        def callback():
            expected_url_combined = '/access_data/download_cdi_results.csv'

            with self.app.test_client() as client:

                with client.session_transaction() as sess:
                    sess['email'] = TEST_EMAIL

                cons_name = 'consolidated_csv'
                cons_value = access_data_controllers.HTML_CHECKBOX_SELECTED
                fmt_name = access_data_controllers.FORMAT_SESSION_ATTR
                fmt_value = 'testFormat'
                url = '/base/access_data/download_cdi_results?'
                resp = client.post(url, data={
                    cons_name: cons_value,
                    fmt_name: fmt_value
                })

                self.assertEqual(
                    flask.session[access_data_controllers.FORMAT_SESSION_ATTR],
                    'testFormat'
                )

                self.assertTrue(session_util.is_waiting_on_download())

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_is_waiting_on_download(self):
        def callback():
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

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_abort_download(self):
        def callback():
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

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_incomplete_add_filter(self):
        def callback():
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

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_add_filter(self):
        def callback():
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

        self.__inject_test_user(callback)
        self.__assert_callback_called()

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

        self.__inject_test_user(callback)
        self.__assert_callback_called()

    def test_access_requests(self):

        self.__executed = False

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
            'cdi_type',
            'hard_of_hearing',
            False
        )]
        test_zip_file = TestZipFile()
        test_csv_file = TestCSVFile()

        def setup_mocks(mock_get_user,
                mock_run_search_query,
                mock_load_presentation,
                mock_report_usage,
                mock_generate_study_report,
                mock_generate_consolidated_study_report,
                callback):

            # Prep return values
            mock_get_user.return_value = TEST_USER
            mock_run_search_query.return_value = query_results
            mock_load_presentation.side_effect = [
                'test_format_spec',
                None,
                'test_format_spec',
                None
            ]
            mock_generate_study_report.side_effect = [
                test_zip_file,
                test_csv_file
            ]
            mock_generate_consolidated_study_report.return_value = test_csv_file

            # Callback
            callback()

            # Test get user
            mock_get_user.assert_any_call(TEST_EMAIL)

            # Test report usage
            self.assertEqual(len(mock_report_usage.mock_calls), 4)
            mock_report_usage.assert_any_call(
                'test_mail',
                'Download Data as zip',
                unittest.mock.ANY
            )
            mock_report_usage.assert_any_call(
                'test_mail',
                'Download Data as zip',
                unittest.mock.ANY
            )

            # Test run search query
            self.assertEqual(len(mock_run_search_query.mock_calls), 4)
            mock_run_search_query.assert_any_call(
                unittest.mock.ANY,
                'snapshots',
                True
            )

            # Test load presentation model
            self.assertEqual(len(mock_load_presentation.mock_calls), 4)
            mock_load_presentation.assert_any_call('test_format')
            mock_load_presentation.assert_any_call('test_format_2')

            # Test generate report study
            self.assertEqual(len(mock_generate_study_report.mock_calls), 1)
            mock_generate_consolidated_study_report.assert_any_call(
                query_results,
                'test_format_spec'
            )

        def test_body():
            self.__executed = True

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

                resp = client.get('/base/access_data/download_cdi_results.zip')
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
                    resp.data.decode('utf-8'),
                    test_zip_file.getvalue()
                )

                with client.session_transaction() as sess:
                    self.assertFalse(session_util.is_waiting_on_download(sess))
                    session_util.set_waiting_on_download(True, sess)

                with client.session_transaction() as sess:
                    sess['format'] = 'test_format_2'

                resp = client.get('/base/access_data/download_cdi_results.zip')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertTrue('presentation format' in sess[ERROR_ATTR])
                    self.assertFalse(session_util.is_waiting_on_download(sess))
                    sess['format'] = 'test_format'
                    session_util.set_waiting_on_download(True, sess)

                resp = client.get('/base/access_data/download_cdi_results.csv')
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
                    resp.data.decode('utf-8'),
                    test_csv_file.getvalue()
                )

                with client.session_transaction() as sess:
                    self.assertFalse(session_util.is_waiting_on_download(sess))
                    session_util.set_waiting_on_download(True, sess)

                with client.session_transaction() as sess:
                    sess['format'] = 'test_format_2'

                resp = client.get('/base/access_data/download_cdi_results.zip')
                self.assertEqual(resp.status_code, 302)

                with client.session_transaction() as sess:
                    self.assertTrue('presentation format' in sess[ERROR_ATTR])
                    self.assertFalse(session_util.is_waiting_on_download(sess))

        def execute(callback):
            with unittest.mock.patch('prog_code.util.user_util.get_user') as mock_get_user:
                with unittest.mock.patch('prog_code.util.filter_util.run_search_query') as mock_run_search_query:
                    with unittest.mock.patch('prog_code.util.db_util.load_presentation_model') as mock_load_presentation:
                        with unittest.mock.patch('prog_code.util.db_util.report_usage') as mock_report_usage:
                            with unittest.mock.patch('prog_code.util.report_util.generate_study_report') as mock_generate_study_report:
                                with unittest.mock.patch('prog_code.util.report_util.generate_consolidated_study_report') as mock_generate_consolidated_study_report:
                                    setup_mocks(
                                        mock_get_user,
                                        mock_run_search_query,
                                        mock_load_presentation,
                                        mock_report_usage,
                                        mock_generate_study_report,
                                        mock_generate_consolidated_study_report,
                                        callback
                                    )

        execute(test_body)
        self.assertTrue(self.__executed)
