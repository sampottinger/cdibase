import mox

import mail_util


class TestMailInstance:

    def send(self, message):
        self.last_message =  message

TEST_MAIL_INSTANCE = TestMailInstance()


class TestMailKeeper:

    def get_mail_instance(self):
        return TEST_MAIL_INSTANCE

    def get_from_addr(self):
        return 'from addr'

TEST_MAIL_KEEPER = TestMailKeeper()


class MailUtilTests(mox.MoxTestBase):

    def test_send_mail_no_keeper(self):
        self.mox.StubOutWithMock(mail_util, 'get_mail_keeper')
        mail_util.get_mail_keeper().AndReturn(None)
        self.mox.ReplayAll()

        mail_util.send_msg('test address', 'test subject', 'test message')

    def test_send_mail_with_keeper(self):
        self.mox.StubOutWithMock(mail_util, 'get_mail_keeper')
        mail_util.get_mail_keeper().AndReturn(TEST_MAIL_KEEPER)
        self.mox.ReplayAll()

        mail_util.send_msg('test address', 'test subject', 'test message')

        last_message = TEST_MAIL_INSTANCE.last_message
        self.assertEqual(last_message.subject, 'test subject')
        self.assertEqual(last_message.sender, 'from addr')
        self.assertEqual(last_message.body, 'test message')
        self.assertEqual(last_message.recipients, ['test address'])
