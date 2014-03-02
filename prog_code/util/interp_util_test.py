import datetime

import mox

from ..struct import models

import interp_util


class InterpUtilTests(mox.MoxTestBase):

    def test_monthdelta(self):
        d1 = datetime.date(2011, 1, 2)
        d2 = datetime.date(2012, 2, 3)
        
        self.assertTrue(abs(interp_util.monthdelta(d1, d2) - 13.04) < 0.01)
        self.assertEqual(interp_util.monthdelta(d1, d1), 0)
        self.assertEqual(interp_util.monthdelta(d2, d1), 0)

    def test_safe_int_interpret(self):
        self.assertEqual(interp_util.safe_int_interpret(None), None)
        self.assertEqual(interp_util.safe_int_interpret('test'), None)
        self.assertEqual(interp_util.safe_int_interpret('123'), 123)
        self.assertEqual(interp_util.safe_int_interpret('123.4'), None)

    def test_safe_float_interpret(self):
        self.assertEqual(interp_util.safe_float_interpret(None), None)
        self.assertEqual(interp_util.safe_float_interpret('test'), None)
        self.assertEqual(interp_util.safe_float_interpret('123'), 123)
        self.assertEqual(interp_util.safe_float_interpret('123.4'), 123.4)

    def test_operator_to_str(self):
        self.assertEqual(interp_util.operator_to_str('lteq'), '<=')
        self.assertEqual(interp_util.operator_to_str('unknown'), '?')

    def test_filter_to_str(self):
        test_filter = models.Filter('operand', 'gteq', 'operator')
        test_str = interp_util.filter_to_str(test_filter)
        self.assertEqual(test_str, 'operand >= operator')
