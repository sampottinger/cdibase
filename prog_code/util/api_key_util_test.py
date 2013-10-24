import mox

import api_key_util
import user_util
import db_util


class APIKeyUtilTests(mox.MoxTestBase):

    def test_interp_csv_field(self):
        result = api_key_util.interp_csv_field('')
        self.assertEqual(result, [])

        result = api_key_util.interp_csv_field('test')
        self.assertEqual(result, ['test'])

        result = api_key_util.interp_csv_field('test,test2')
        self.assertEqual(result, ['test', 'test2'])

        result = api_key_util.interp_csv_field('test,test2,')
        self.assertEqual(result, ['test', 'test2', ''])

    def test_get_if_avail(self):
        result = api_key_util.get_if_avail(['1', '2', '3'], 2)
        self.assertEqual(result, '3')

        result = api_key_util.get_if_avail(['1', '2'], 2, 'DEFAULT')
        self.assertEqual(result, 'DEFAULT')

    def test_generate_new_api_key(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')

        db_util.get_api_key(mox.IsA(basestring)).AndReturn(None)
        db_util.get_api_key(mox.IsA(basestring)).AndReturn(True)
        db_util.get_api_key(mox.IsA(basestring)).AndReturn(True)
        db_util.get_api_key(mox.IsA(basestring)).AndReturn(None)

        self.mox.ReplayAll()

        api_key_util.generate_new_api_key()
        api_key_util.generate_new_api_key()


    def test_create_new_api_key(self):
        self.mox.StubOutWithMock(db_util, 'get_api_key')
        self.mox.StubOutWithMock(db_util, 'delete_api_key')
        self.mox.StubOutWithMock(db_util, 'create_new_api_key')

        db_util.get_api_key('123').AndReturn(True)
        db_util.delete_api_key('123')
        db_util.get_api_key(mox.IsA(basestring)).AndReturn(None)
        db_util.create_new_api_key('123', mox.IsA(basestring))

        self.mox.ReplayAll()

        api_key_util.create_new_api_key('123')
