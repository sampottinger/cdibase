import unittest

import mox

import constants
import csv_import_util


class UploadParserAutomatonTests(mox.MoxTestBase):

    def setUp(self):
        self.__test_automaton = csv_import_util.UploadParserAutomaton()
    
    def test_enter_error_state(self):
        self.__test_automaton.enter_error_state('test error')
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'test error'
        )

    def test_sanity_check_pass(self):
        self.assertTrue(self.__test_automaton.sanity_check(['', 'test'],
            'test', 1))
        self.assertNotEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertNotEqual(
            self.__test_automaton.get_error(),
            'Expected \"test\" on row 1 but found \"test\".'
        )

    def test_sanity_check_fail(self):
        self.assertFalse(self.__test_automaton.sanity_check(['', 'test'],
            'other', 1))
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'Expected \"other\" on row 1 but found \"test\".'
        )

    def test_safe_parse_float_pass(self):
        self.assertTrue(self.__test_automaton.safe_parse_float('5.5', 1))

    def test_safe_parse_float_fail(self):
        self.assertFalse(self.__test_automaton.safe_parse_float('a', 1), 1)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'Was expecting a number but found \"a\" on row 1.'
        )

    def test_safe_parse_int_pass(self):
        self.assertTrue(self.__test_automaton.safe_parse_int('5', 1))

    def test_safe_parse_int_fail(self):
        self.assertFalse(self.__test_automaton.safe_parse_int('a', 1), 1)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'Was expecting an integer but found \"a\" on row 1.'
        )

    def test_safe_parse_date_pass(self):
        self.assertEqual(
            self.__test_automaton.safe_parse_date('2013/01/2', 1),
            '2013/1/2'
        )
        self.assertEqual(
            self.__test_automaton.safe_parse_date('2013/10/2', 1),
            '2013/10/2'
        )

    def test_safe_parse_date_fail(self):
        self.assertFalse(self.__test_automaton.safe_parse_date('a', 1), 1)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'Was expecting a date but found \"a\" on row 1.'
        )

    def test_safe_parse_date_malformed(self):
        self.assertFalse(
            self.__test_automaton.safe_parse_date('a/11/2012', 1),
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'Found a date (a/11/2012) but was expecting form YYYY/MM/DD on '\
            'row 1.'
        )

    def test_safe_parse_date_invalid(self):
        self.assertFalse(
            self.__test_automaton.safe_parse_date('10/11/2012', 1),
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'Found a date (10/11/2012) but was expecting form YYYY/MM/DD on '\
            'row 1.'
        )

    def test_step(self):
        self.assertEqual(len(self.__test_automaton.get_prototypes()), 0)
        self.__test_automaton.step(
            ['', 'Child\'s ID (from database)', '123', '456', '789'],
            1
        )
        self.assertEqual(len(self.__test_automaton.get_prototypes()), 3)

    def test_parse_child_db_id(self):
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_CHILD_DB_ID)
        self.__test_automaton.parse_child_db_id(
            ['', 'Child\'s ID (from database)', '123', '456', '789'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_CHILD_STUDY_ID
        )

        self.assertEqual(prototypes[0]['child_id'], 123)
        self.assertEqual(prototypes[1]['child_id'], 456)
        self.assertEqual(prototypes[2]['child_id'], 789)

    def test_parse_child_db_id_invalid(self):
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_CHILD_DB_ID)
        self.__test_automaton.parse_child_db_id(
            ['', 'Child\'s ID (from database)', '123a', '456', '789'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_child_db_id_wrong_label(self):
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_CHILD_DB_ID)
        self.__test_automaton.parse_child_db_id(
            ['', 'Child\'s ID (from daabase)', '123', '456', '789'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_child_study_id(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_CHILD_STUDY_ID
        )
        self.__test_automaton.parse_child_study_id(
            ['', 'Name / Number', '02', '46', '80'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_STUDY_AND_SOURCE
        )

        self.assertEqual(prototypes[0]['study_id'], '02')
        self.assertEqual(prototypes[1]['study_id'], '46')
        self.assertEqual(prototypes[2]['study_id'], '80')

    def test_parse_child_study_id_wrong_label(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_CHILD_STUDY_ID
        )
        self.__test_automaton.parse_child_study_id(
            ['', 'Name Number', '02', '46', '80'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_study_and_source(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_STUDY_AND_SOURCE
        )
        self.__test_automaton.parse_study_and_source(
            ['', 'Study / Source', 'Study1', 'Study2', 'Study3'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_GENDER
        )

        self.assertEqual(prototypes[0]['study'], 'Study1')
        self.assertEqual(prototypes[1]['study'], 'Study2')
        self.assertEqual(prototypes[2]['study'], 'Study3')

    def test_parse_study_and_source_wrong_label(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_STUDY_AND_SOURCE
        )
        self.__test_automaton.parse_study_and_source(
            ['', 'Study Source', 'Study1', 'Study2', 'Study3'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_gender_pass(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_GENDER
        )
        self.__test_automaton.parse_gender(
            ['', 'Gender', 'M', 'F', 'O'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_AGE
        )

        self.assertEqual(prototypes[0]['gender'], constants.MALE)
        self.assertEqual(prototypes[1]['gender'], constants.FEMALE)
        self.assertEqual(prototypes[2]['gender'], constants.OTHER_GENDER)

    def test_parse_gender_invalid(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_GENDER
        )
        self.__test_automaton.parse_gender(
            ['', 'Gender', '5', 'F', 'O'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_gender_wrong_label(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_GENDER
        )
        self.__test_automaton.parse_gender(
            ['', 'Genders', 'M', 'F', 'O'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_age(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_AGE)
        self.__test_automaton.parse_age(
            ['', 'Age (months)', '123.1', '456.2', '789.3'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_DATE_OF_BIRTH
        )

        self.assertEqual(prototypes[0]['age'], 123.1)
        self.assertEqual(prototypes[1]['age'], 456.2)
        self.assertEqual(prototypes[2]['age'], 789.3)

    def test_parse_age_invalid(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_AGE)
        self.__test_automaton.parse_age(
            ['', 'Age (months)', 'a 123.1', '456.2', '789.3'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_age_wrong_label(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_AGE)
        self.__test_automaton.parse_age(
            ['', 'Age', '123.1', '456.2', '789.3'],
            1
        ) 
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_date_of_birth(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_DATE_OF_BIRTH
        )
        self.__test_automaton.parse_date_of_birth(
            ['', 'Date of Birth', '2013/01/02', '2013/02/03', '2013/04/05'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_DATE_OF_SESSION
        )

        self.assertEqual(prototypes[0]['birthday'], '2013/1/2')
        self.assertEqual(prototypes[1]['birthday'], '2013/2/3')
        self.assertEqual(prototypes[2]['birthday'], '2013/4/5')

    def test_parse_date_of_birth_invalid(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_DATE_OF_BIRTH
        )
        self.__test_automaton.parse_date_of_birth(
            ['', 'Date of Birth', '05/01/02', '2013/02/03', '2013/04/05'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_date_of_birth_wrong_label(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_DATE_OF_BIRTH
        )
        self.__test_automaton.parse_date_of_birth(
            ['', 'Dae of Birth', '2013/01/02', '2013/02/03', '2013/04/05'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_date_of_session(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_DATE_OF_SESSION
        )
        self.__test_automaton.parse_date_of_session(
            ['', 'Date of Session', '2013/01/02', '2013/02/03', '2013/04/05'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_SESSION_NUM
        )

        self.assertEqual(prototypes[0]['session_date'], '2013/1/2')
        self.assertEqual(prototypes[1]['session_date'], '2013/2/3')
        self.assertEqual(prototypes[2]['session_date'], '2013/4/5')

    def test_parse_date_of_session_wrong_label(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_DATE_OF_SESSION
        )
        self.__test_automaton.parse_date_of_session(
            ['', 'Date of Sessin', '2013/01/02', '2013/02/03', '2013/04/05'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_date_of_session_invalid(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_DATE_OF_SESSION
        )
        self.__test_automaton.parse_date_of_session(
            ['', 'Date of Session', '2013/01/02a', '2013/02/03', '2013/04/05'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_session_num(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_SESSION_NUM)
        self.__test_automaton.parse_session_num(
            ['', 'Session #', '123', '456', '789'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_TOTAL_SESSION_NUM
        )

        self.assertEqual(prototypes[0]['session_num'], 123)
        self.assertEqual(prototypes[1]['session_num'], 456)
        self.assertEqual(prototypes[2]['session_num'], 789)

    def test_parse_total_session_num(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_TOTAL_SESSION_NUM)
        self.__test_automaton.parse_total_session_num(
            ['', 'Total # of Sessions', '123', '456', '789'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_WORDS_SPOKEN
        )

        self.assertEqual(prototypes[0]['total_num_sessions'], 123)
        self.assertEqual(prototypes[1]['total_num_sessions'], 456)
        self.assertEqual(prototypes[2]['total_num_sessions'], 789)

    def test_parse_words_spoken(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_WORDS_SPOKEN)
        self.__test_automaton.parse_words_spoken(
            ['', 'Words Spoken', '123', '456', '789'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_ITEMS_EXCLUDED
        )

        self.assertEqual(prototypes[0]['words_spoken'], 123)
        self.assertEqual(prototypes[1]['words_spoken'], 456)
        self.assertEqual(prototypes[2]['words_spoken'], 789)

    def test_parse_items_excluded(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_ITEMS_EXCLUDED)
        self.__test_automaton.parse_items_excluded(
            ['', 'Items Excluded', '123', '456', '789'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_PERCENTILE
        )

        self.assertEqual(prototypes[0]['items_excluded'], 123)
        self.assertEqual(prototypes[1]['items_excluded'], 456)
        self.assertEqual(prototypes[2]['items_excluded'], 789)

    def test_parse_percentile(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_PERCENTILE)
        self.__test_automaton.parse_percentile(
            ['', 'Percentile', '80.1', '90.2', '95.3'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_EXTRA_CATEGORIES
        )

        self.assertEqual(prototypes[0]['percentile'], 80.1)
        self.assertEqual(prototypes[1]['percentile'], 90.2)
        self.assertEqual(prototypes[2]['percentile'], 95.3)

    def test_parse_percentile_invalid(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_PERCENTILE)
        self.__test_automaton.parse_percentile(
            ['', 'Percentile', '100.1', '90.2', '95.3'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_extra_categories(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_EXTRA_CATEGORIES)
        self.__test_automaton.parse_extra_categories(
            ['', 'Extra Categories?', 'Y', 'N', 'Y'],
            1
        )
        
        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes), 3)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_SECTION_WORD_HEADING
        )

        self.assertEqual(prototypes[0]['extra_categories'],
            constants.EXPLICIT_TRUE)
        self.assertEqual(prototypes[1]['extra_categories'],
            constants.EXPLICIT_FALSE)
        self.assertEqual(prototypes[2]['extra_categories'],
            constants.EXPLICIT_TRUE)

    def test_parse_extra_categories_invalid(self):
        self.__test_automaton.set_prototypes([{}, {}, {}])
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_EXTRA_CATEGORIES)
        self.__test_automaton.parse_extra_categories(
            ['', 'Extra Categories?', '1', 'N', 'Y'],
            1
        )
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_section_word_heading(self):
        self.__test_automaton.set_state(
            csv_import_util.STATE_PARSE_SECTION_WORD_HEADING)
        self.__test_automaton.set_prototypes([{}, {}, {}])

        self.__test_automaton.parse_section_word_heading(
            ['Section', 'Word'],
            1
        )

        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes[0]['words']), 0)
        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_WORDS
        )

    def test_parse_words(self):
        self.__test_automaton.set_state(csv_import_util.STATE_PARSE_WORDS)
        self.__test_automaton.set_prototypes([
            {'words': []}, {'words': []}, {'words': []}
        ])

        self.__test_automaton.parse_words(['1', 'test', '1', '0', '1'], 1)

        self.assertEqual(
            self.__test_automaton.get_state(),
            csv_import_util.STATE_PARSE_WORDS
        )

        prototypes = self.__test_automaton.get_prototypes()
        self.assertEqual(len(prototypes[0]['words']), 1)
        
        self.assertEqual(prototypes[0]['words'][0]['word'], 'test')
        self.assertEqual(prototypes[0]['words'][0]['val'],
            constants.EXPLICIT_TRUE)
        
        self.assertEqual(prototypes[1]['words'][0]['word'], 'test')
        self.assertEqual(prototypes[1]['words'][0]['val'],
            constants.EXPLICIT_FALSE)
        
        self.assertEqual(prototypes[2]['words'][0]['word'], 'test')
        self.assertEqual(prototypes[2]['words'][0]['val'],
            constants.EXPLICIT_TRUE)

        self.__test_automaton.parse_words(['1', 'again', '0', '1', '0'], 2)
        self.assertEqual(prototypes[0]['words'][1]['word'], 'again')
        self.assertEqual(prototypes[0]['words'][1]['val'],
            constants.EXPLICIT_FALSE)
        
        self.assertEqual(prototypes[1]['words'][1]['word'], 'again')
        self.assertEqual(prototypes[1]['words'][1]['val'],
            constants.EXPLICIT_TRUE)
        
        self.assertEqual(prototypes[2]['words'][1]['word'], 'again')
        self.assertEqual(prototypes[2]['words'][1]['val'],
            constants.EXPLICIT_FALSE)


if __name__ == '__main__':
    unittest.main()
