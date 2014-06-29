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

import mox

import db_util
import mail_util
import parent_account_util

TEST_PARENT_FORM = collections.namedtuple(
    'TestParentForm',
    ['child_name', 'form_id', 'parent_email']
)


class ParentAccountUtilTests(mox.MoxTestBase):

    def test_is_likely_email_address(self):
        test_email = 'Test Parent at somewhere.com'
        test_result = parent_account_util.is_likely_email_address(test_email)
        self.assertFalse(test_result)

        test_email = 'Test.Parent@somewhere.com'
        test_result = parent_account_util.is_likely_email_address(test_email)
        self.assertTrue(test_result)

    def test_generate_unique_mcdi_form_id(self):
        self.mox.StubOutWithMock(db_util, 'get_parent_form_by_id')

        db_util.get_parent_form_by_id(mox.IsA(basestring)).AndReturn(True)
        db_util.get_parent_form_by_id(mox.IsA(basestring)).AndReturn(True)
        db_util.get_parent_form_by_id(mox.IsA(basestring)).AndReturn(None)

        self.mox.ReplayAll()

        parent_account_util.generate_unique_mcdi_form_id()

    def test_send_mcdi_email(self):
        self.mox.StubOutWithMock(mail_util, 'send_msg')

        form_url = parent_account_util.URL_TEMPLATE % 'url'
        msg = parent_account_util.MCDI_EMAIL_TEMPLATE % ('child', form_url)

        mail_util.send_msg(
            'test email',
            parent_account_util.MCDI_EMAIL_SUBJECT,
            msg
        )

        self.mox.ReplayAll()

        test_form = TEST_PARENT_FORM('child', 'url', 'test email')
        parent_account_util.send_mcdi_email(test_form)

