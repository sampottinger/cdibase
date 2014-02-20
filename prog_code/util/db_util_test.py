import re

import mox

import db_util


class DBUtilTests(mox.MoxTestBase):
    
    def test_clean_up_date(self):
        self.assertEqual(db_util.clean_up_date('1992/1/10'), '1992/01/10')
        self.assertEqual(db_util.clean_up_date('1992/01/10'), '1992/01/10')
