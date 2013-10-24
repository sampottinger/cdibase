import re

import mox

import file_util


class FileUtilTests(mox.MoxTestBase):

    def test_generate_filename(self):
        filename = file_util.generate_filename(
            '.csv',
            length=3,
            chars=['a', 'b', 'c']
        )
        self.assertEqual(len(filename), 7)

        chars_regex = re.compile('[abc]{3}\.csv')
        self.assertIsNotNone(chars_regex.match(filename))

    def test_generate_unique_filename(self):
        self.mox.StubOutWithMock(file_util, 'upload_exists')

        file_util.upload_exists(mox.IsA(basestring)).AndReturn(True)
        file_util.upload_exists(mox.IsA(basestring)).AndReturn(True)
        file_util.upload_exists(mox.IsA(basestring)).AndReturn(False)

        self.mox.ReplayAll()

        filename = file_util.generate_unique_filename('.csv')
        self.assertIn('.csv', filename)

    def test_allowed_file(self):
        self.assertTrue(file_util.allowed_file('test.csv'))
        self.assertFalse(file_util.allowed_file('test.exe'))
        self.assertFalse(file_util.allowed_file('test'))
