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

