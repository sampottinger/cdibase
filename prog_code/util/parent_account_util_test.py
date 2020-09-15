"""Tests for utility functions used in managing parent accounts.

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
import collections
import unittest
import unittest.mock

import prog_code.util.db_util as db_util
import prog_code.util.mail_util as mail_util
import prog_code.util.parent_account_util as parent_account_util

TEST_PARENT_FORM = collections.namedtuple(
    'TestParentForm',
    ['child_name', 'form_id', 'parent_email']
)


class ParentAccountUtilTests(unittest.TestCase):

    def test_is_likely_email_address(self):
        test_email = 'Test Parent at somewhere.com'
        test_result = parent_account_util.is_likely_email_address(test_email)
        self.assertFalse(test_result)

        test_email = 'Test.Parent@somewhere.com'
        test_result = parent_account_util.is_likely_email_address(test_email)
        self.assertTrue(test_result)

    def test_generate_unique_cdi_form_id(self):
        with unittest.mock.patch('prog_code.util.db_util.get_parent_form_by_id') as mock:
            mock.side_effect = [True, True, None]
            parent_account_util.generate_unique_cdi_form_id()
            self.assertEqual(len(mock.mock_calls), 3)

    def test_send_cdi_email(self):
        with unittest.mock.patch('prog_code.util.mail_util.send_msg') as mock:
            form_url = parent_account_util.URL_TEMPLATE % 'url'
            msg = parent_account_util.CDI_EMAIL_TEMPLATE % ('child', form_url)

            test_form = TEST_PARENT_FORM('child', 'url', 'test email')
            parent_account_util.send_cdi_email(test_form)

            mock.assert_called_with(
                'test email',
                parent_account_util.CDI_EMAIL_SUBJECT,
                msg
            )
