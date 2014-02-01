import mox

import constants
import oper_interp


class OperUtilTests(mox.MoxTestBase):

    def test_raw_interpret_field(self):
        target_field = oper_interp.RawInterpretField('Test1')
        self.assertEqual(target_field.interpret_value('Test')[0], 'Test')
        self.assertEqual(target_field.get_field_name(), 'Test1')

    def test_gender_field(self):
        target_field = oper_interp.GenderField('Test2')

        target_val = target_field.interpret_value('Male')[0]
        self.assertEqual(target_val, constants.MALE)

        target_val = target_field.interpret_value('gIrl')[0]
        self.assertEqual(target_val, constants.FEMALE)

        target_val = target_field.interpret_value('trAns')[0]
        self.assertEqual(target_val, constants.OTHER_GENDER)

        self.assertEqual(target_field.get_field_name(), 'Test2')

    def test_boolean_field(self):
        target_field = oper_interp.BooleanField('Test3')

        target_val = target_field.interpret_value('True')[0]
        self.assertEqual(target_val, True)

        target_val = target_field.interpret_value('nO')[0]
        self.assertEqual(target_val, False)

        target_val = target_field.interpret_value('orig')[0]
        self.assertEqual(target_val, 'orig')

        self.assertEqual(target_field.get_field_name(), 'Test3')

    def test_numerical_field(self):
        target_field = oper_interp.NumericalField('Test4')

        target_val = target_field.interpret_value('1')[0]
        self.assertEqual(target_val, 1)

        target_val = target_field.interpret_value('1.23')[0]
        self.assertEqual(target_val, 1.23)

        self.assertEqual(target_field.get_field_name(), 'Test4')
