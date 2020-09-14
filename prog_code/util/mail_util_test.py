"""Tests for email utility functions.

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

import prog_code.util.mail_util as mail_util


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


class MailUtilTests(unittest.TestCase):

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
        self.assertEqual(last_message.recipients, ['testaddress'])
