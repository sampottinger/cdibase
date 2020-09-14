"""Tests for utility functions used in CSV imports.

Copyright (C) 2016 A. Samuel Pottinger ('Sam Pottinger')

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

from ..struct import models

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util
import prog_code.util.new_csv_import_util as new_csv_import_util
import prog_code.util.math_util as math_util
import prog_code.util.recalc_util as recalc_util


CORRECT_TEST_HEADER_VALUES = [
    'database id',
    'child id',
    'study id',
    'study',
    'gender',
    'age',
    'birthday',
    'session date',
    'session num',
    'total num sessions',
    'words spoken',
    'items excluded',
    'percentile',
    'extra categories',
    'revision',
    'languages',
    'num languages',
    'mcdi type',
    'hard of hearing',
    'deleted',
    'word1',
    'word2',
    'word3',
    'word4'
]


class FakePercentileTable:

    def __init__(self, details):
        self.details = details


class NewUploadParserAutomatonTests(unittest.TestCase):

    def setUp(self):
        self.__adapter = recalc_util.CachedMCDIAdapter()

        self.__test_automaton = new_csv_import_util.UploadParserAutomaton(
            self.__adapter
        )

        self.__callback_called = False

    def __setup_test_cdi(self, callback, run_automaton_actions=True):
        with unittest.mock.patch('prog_code.util.db_util.load_mcdi_model') as mock:
            mock.return_value = models.MCDIFormat(
                'test MCDI type',
                'test_mcdi_type',
                'test_mcdi_type.yaml',
                {
                    'options': [
                        {'value': 0},
                        {'value': 1}
                    ],
                    'categories': [
                        {'words': ['word1', 'word2']},
                        {'words': ['word3', 'word4']}
                    ],
                    'count_as_spoken': [1]
                }
            )

            if run_automaton_actions:
                self.__test_automaton.parse_header(CORRECT_TEST_HEADER_VALUES)
                self.__test_automaton.parse_cdi_type('test_mcdi_type')

            callback()

            mock.assert_called_with('test_mcdi_type')

    def __setup_for_parse_with_percentile(self, callback, expect_percent_calc=True):
        with unittest.mock.patch('prog_code.util.recalc_util.recalculate_percentile_raw') as mock:

            def outer_callback():
                if expect_percent_calc:
                    mock.return_value = 99

                callback()

            self.__setup_test_cdi(outer_callback, False)

            if expect_percent_calc:
                mock.assert_called_with(
                    self.__adapter,
                    'test_mcdi_type',
                    constants.MALE,
                    3,
                    unittest.mock.ANY
                )

    def test_state_error(self):
        self.__test_automaton.enter_error_state('test error')
        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )
        self.assertEqual(
            self.__test_automaton.get_error(),
            'test error'
        )

    def test_state_parse_header_pass_db_id(self):
        self.__test_automaton.parse_header(CORRECT_TEST_HEADER_VALUES)
        self.assertTrue(self.__test_automaton.expects_db_id_field())

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_DATABASE_ID
        )

    def test_state_parse_header_pass_no_db_id(self):
        test_header_values = [
            'child id',
            'study id',
            'study',
            'gender',
            'age',
            'birthday',
            'session date',
            'session num',
            'total num sessions',
            'words spoken',
            'items excluded',
            'percentile',
            'extra categories',
            'revision',
            'languages',
            'num languages',
            'mcdi type',
            'hard of hearing',
            'deleted',
            'word1',
            'word2',
            'word3',
            'word4'
        ]

        self.__test_automaton.parse_header(test_header_values)
        self.assertFalse(self.__test_automaton.expects_db_id_field())

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_CHILD_ID
        )


    def test_state_parse_header_fail_value(self):
        test_header_values = [
            'child id invalid',
            'study id',
            'study',
            'gender',
            'age',
            'birthday',
            'session date',
            'session num',
            'total num sessions',
            'words spoken',
            'items excluded',
            'percentile',
            'extra categories',
            'revision',
            'languages',
            'num languages',
            'mcdi type',
            'hard of hearing',
            'deleted',
            'word1',
            'word2',
            'word3',
            'word4'
        ]

        self.__test_automaton.parse_header(test_header_values)

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )


    def test_state_parse_database_id_empty(self):
        self.__test_automaton.parse_database_id('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_CHILD_ID
        )

    def test_state_parse_database_id_specify_valid_number(self):
        self.__test_automaton.parse_database_id('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_CHILD_ID
        )

    def test_state_parse_database_id_specify_valid_alpha(self):
        self.__test_automaton.parse_database_id('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_CHILD_ID
        )

    def test_state_parse_child_id_valid_non_empty(self):
        self.__test_automaton.parse_child_id('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_STUDY_ID
        )

    def test_state_parse_child_id_valid_empty(self):
        self.__test_automaton.parse_child_id('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_STUDY_ID
        )

    def test_state_parse_study_id_valid(self):
        self.__test_automaton.parse_study_id('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_STUDY
        )

    def test_state_parse_study_id_invalid(self):
        self.__test_automaton.parse_study_id('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_study_valid(self):
        self.__test_automaton.parse_study('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_GENDER
        )

    def test_state_parse_study_invalid(self):
        self.__test_automaton.parse_study('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_gender_valid_full_cap(self):
        self.__test_automaton.parse_gender('Male')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_AGE
        )

    def test_state_parse_gender_valid_full_lower(self):
        self.__test_automaton.parse_gender('other')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_AGE
        )

    def test_state_parse_gender_valid_full_abbrev(self):
        self.__test_automaton.parse_gender('female')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_AGE
        )

    def test_state_parse_gender_invalid_value(self):
        self.__test_automaton.parse_gender('Invalid')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_gender_invalid_empty(self):
        self.__test_automaton.parse_gender('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_age_valid(self):
        self.__test_automaton.parse_age('23.456')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_BIRTHDAY
        )

    def test_state_parse_age_valid_empty(self):
        self.__test_automaton.parse_age('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_BIRTHDAY
        )

    def test_state_parse_age_invalid_value_mixed(self):
        self.__test_automaton.parse_age('123.456a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_age_invalid_value_range(self):
        self.__test_automaton.parse_age('-123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_age_invalid_value_prefix(self):
        self.__test_automaton.parse_age('0123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_age_valid_value_empty(self):
        self.__test_automaton.parse_age('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_BIRTHDAY
        )

    def test_state_parse_birthday_valid(self):
        self.__test_automaton.parse_birthday('2009-02-16')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_SESSION_DATE
        )

    def test_state_parse_birthday_invalid_empty(self):
        self.__test_automaton.parse_birthday('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_birthday_invalid_format(self):
        self.__test_automaton.parse_birthday('aaaa-bb-cc')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_birthday_invalid_value(self):
        self.__test_automaton.parse_birthday('2009-02-32')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_date_valid(self):
        self.__test_automaton.parse_session_date('2011-04-13')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_SESSION_NUM
        )

    def test_state_parse_session_date_valid(self):
        self.__test_automaton.parse_session_date('2011/04/13')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_SESSION_NUM
        )

    def test_state_parse_session_date_invalid_empty(self):
        self.__test_automaton.parse_session_date('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_date_invalid_format(self):
        self.__test_automaton.parse_session_date('a678-12-34')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_date_invalid_value(self):
        self.__test_automaton.parse_session_date('2009-02-32')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_num_valid(self):
        self.__test_automaton.parse_session_num('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_TOTAL_NUM_SESSIONS
        )

    def test_state_parse_session_num_invalid_type(self):
        self.__test_automaton.parse_session_num('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_num_invalid_value(self):
        self.__test_automaton.parse_session_num('-1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_num_invalid_prefix(self):
        self.__test_automaton.parse_session_num('0123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_session_num_valid_empty(self):
        self.__test_automaton.parse_session_num('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_TOTAL_NUM_SESSIONS
        )

    def test_state_parse_total_num_sessions_valid(self):
        self.__test_automaton.parse_total_num_sessions('12')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_WORDS_SPOKEN
        )

    def test_state_parse_total_num_sessions_invalid_empty(self):
        self.__test_automaton.parse_total_num_sessions('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_total_num_sessions_invalid_type(self):
        self.__test_automaton.parse_total_num_sessions('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_total_num_sessions_invalid_prefix(self):
        self.__test_automaton.parse_total_num_sessions('0123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_total_num_sessions_invalid_value_neg(self):
        self.__test_automaton.parse_total_num_sessions('-1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_total_num_sessions_invalid_value_zero(self):
        self.__test_automaton.parse_total_num_sessions('0')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_words_spoken_valid(self):
        self.__test_automaton.parse_spoken_words('123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_ITEMS_EXCLUDED
        )

    def test_state_parse_words_spoken_invalid_type(self):
        self.__test_automaton.parse_spoken_words('a123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_words_spoken_invalid_value(self):
        self.__test_automaton.parse_spoken_words('-1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_words_spoken_invalid_value_prefix(self):
        self.__test_automaton.parse_spoken_words('0123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_words_spoken_valid_value_empty(self):
        self.__test_automaton.parse_spoken_words('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_ITEMS_EXCLUDED
        )

    def test_state_parse_items_excluded_valid(self):
        self.__test_automaton.parse_excluded_items('123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_PERCENTILE
        )

    def test_state_parse_items_excluded_invalid_value_prefix(self):
        self.__test_automaton.parse_excluded_items('0123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_items_excluded_invalid_value_type(self):
        self.__test_automaton.parse_excluded_items('a123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_items_excluded_invalid_value_range(self):
        self.__test_automaton.parse_excluded_items('-123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_items_excluded_invalid_value_empty(self):
        self.__test_automaton.parse_excluded_items('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_PERCENTILE
        )

    def test_state_parse_percentile_valid_provided(self):
        self.__test_automaton.parse_percentile('78.9')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_EXTRA_CATEGORIES
        )

    def test_state_parse_percentile_valid_notprovided(self):
        self.__test_automaton.parse_percentile('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_EXTRA_CATEGORIES
        )

    def test_state_parse_percentile_invalid_type(self):
        self.__test_automaton.parse_percentile('a78.9')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_percentile_invalid_prefix(self):
        self.__test_automaton.parse_percentile('078.9')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_percentile_invalid_range_low(self):
        self.__test_automaton.parse_percentile('-10')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_percentile_invalid_range_high(self):
        self.__test_automaton.parse_percentile('101')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_extra_categories_valid(self):
        self.__test_automaton.parse_extra_categories('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_REVISION
        )

    def test_state_parse_extra_categories_invalid_prefix(self):
        self.__test_automaton.parse_extra_categories('01')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_extra_categories_invalid_type(self):
        self.__test_automaton.parse_extra_categories('a1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_extra_categories_invalid_range(self):
        self.__test_automaton.parse_extra_categories('-1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_extra_categories_invalid_empty(self):
        self.__test_automaton.parse_extra_categories('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_REVISION
        )

    def test_state_parse_revision_valid(self):
        self.__test_automaton.parse_revision('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_LANGUAGES
        )

    def test_state_parse_revision_valid_empty(self):
        self.__test_automaton.parse_revision('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_LANGUAGES
        )

    def test_state_parse_revision_invalid_type(self):
        self.__test_automaton.parse_revision('a1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_revision_invalid_prefix(self):
        self.__test_automaton.parse_revision('01')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_revision_invalid_range(self):
        self.__test_automaton.parse_revision('-1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_languages_valid(self):
        self.__test_automaton.parse_languages('english')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_NUM_LANGUAGES
        )

    def test_state_parse_languages_valid_list(self):
        self.__test_automaton.parse_languages('english,spanish')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_NUM_LANGUAGES
        )

    def test_state_parse_languages_invalid_empty(self):
        self.__test_automaton.parse_languages('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_num_languages_valid(self):
        self.__test_automaton.parse_num_languages('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_MCDI_TYPE
        )

    def test_state_parse_num_languages_valid_empty(self):
        self.__test_automaton.parse_num_languages('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_MCDI_TYPE
        )

    def test_state_parse_num_languages_invalid_type(self):
        self.__test_automaton.parse_num_languages('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_num_languages_invalid_prefix(self):
        self.__test_automaton.parse_num_languages('0123')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_num_languages_invalid_value(self):
        self.__test_automaton.parse_num_languages('-1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_mcdi_type_valid(self):
        def callback():
            self.__callback_called = True
            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_PARSE_HARD_OF_HEARING
            )

        self.__setup_test_cdi(callback)
        self.assertTrue(self.__callback_called)

    def test_state_parse_mcdi_type_invalid(self):
        with unittest.mock.patch('prog_code.util.db_util.load_mcdi_model') as mock:
            mock.return_value = None

            self.__test_automaton.parse_header(CORRECT_TEST_HEADER_VALUES)
            self.__test_automaton.parse_cdi_type('other_test_mcdi_type')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

            mock.assert_called_with('other_test_mcdi_type')

    def test_state_parse_mcdi_type_incorrect_words(self):
        with unittest.mock.patch('prog_code.util.db_util.load_mcdi_model') as mock:

            mock.return_value = models.MCDIFormat(
                'test MCDI type',
                'test_mcdi_type',
                'test_mcdi_type.yaml',
                {
                    'options': [
                        {'value': 0},
                        {'value': 1}
                    ],
                    'categories': [
                        {'words': ['word1', 'word2']},
                        {'words': ['word3', 'word4']}
                    ],
                    'count_as_spoken': [1]
                }
            )

            self.__test_automaton.parse_header([
                'database id',
                'child id',
                'study id',
                'study',
                'gender',
                'age',
                'birthday',
                'session date',
                'session num',
                'total num sessions',
                'words spoken',
                'items excluded',
                'percentile',
                'extra categories',
                'revision',
                'languages',
                'num languages',
                'mcdi type',
                'hard of hearing',
                'deleted',
                'word1',
                'word2',
                'word3',
                'wor5'
            ])

            self.__test_automaton.parse_cdi_type('test_mcdi_type')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

            mock.assert_called_with('test_mcdi_type')

    def test_state_parse_hard_of_hearing_valid_number(self):
        self.__test_automaton.parse_hard_of_hearing('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_DELETED
        )

    def test_state_parse_hard_of_hearing_valid_letter(self):
        self.__test_automaton.parse_hard_of_hearing('n')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_DELETED
        )

    def test_state_parse_hard_of_hearing_invalid_empty(self):
        self.__test_automaton.parse_hard_of_hearing('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_hard_of_hearing_invalid_value(self):
        self.__test_automaton.parse_hard_of_hearing('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_deleted_valid_number(self):
        self.__test_automaton.parse_deleted('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_START_WORDS
        )

    def test_state_parse_deleted_valid_letter(self):
        self.__test_automaton.parse_deleted('n')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_START_WORDS
        )

    def test_state_parse_deleted_invalid_empty(self):
        self.__test_automaton.parse_deleted('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_deleted_invalid_value(self):
        self.__test_automaton.parse_deleted('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_start_words_valid(self):
        self.__setup_test_cdi()
        self.__test_automaton.parse_word_start('1')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_PARSE_WORDS
        )

    def test_state_parse_start_words_invalid_range(self):
        self.__setup_test_cdi()
        self.__test_automaton.parse_word_start('2')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_start_words_invalid_type(self):
        self.__setup_test_cdi()
        self.__test_automaton.parse_word_start('a')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_state_parse_start_words_invalid_empty(self):
        self.__setup_test_cdi()
        self.__test_automaton.parse_word_start('')

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )


    def test_state_parse_start_words_valid(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.parse_word_start('1')
            self.__test_automaton.parse_word('1')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_PARSE_WORDS
            )

        self.__setup_test_cdi(callback)
        self.assertTrue(self.__callback_called)

    def test_state_parse_start_words_invalid_range(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.parse_word_start('1')
            self.__test_automaton.parse_word('2')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_test_cdi(callback)
        self.assertTrue(self.__callback_called)

    def test_state_parse_start_words_invalid_type(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.parse_word_start('1')
            self.__test_automaton.parse_word('a')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_test_cdi(callback)
        self.assertTrue(self.__callback_called)

    def test_state_parse_start_words_invalid_empty(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.parse_word_start('1')
            self.__test_automaton.parse_word('')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_test_cdi(callback)
        self.assertTrue(self.__callback_called)

    def test_state_parse_start_words_exhaust(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.parse_word_start('1')
            self.__test_automaton.parse_word('0')
            self.__test_automaton.parse_word('1')
            self.__test_automaton.parse_word('0')
            self.__test_automaton.parse_word('0')

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_test_cdi(callback)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_valid_provided_percentile(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 1)
            record = records[0]

            metadata = record.meta
            self.assertEqual(metadata.child_id, 'test_child_id')
            self.assertEqual(metadata.study_id, 'test_study_id')
            self.assertEqual(metadata.study, 'test_study')
            self.assertEqual(metadata.gender, constants.MALE)
            self.assertEqual(metadata.age, 24)
            self.assertEqual(metadata.birthday, '2014/12/24')
            self.assertEqual(metadata.session_date, '2016/12/24')
            self.assertEqual(metadata.session_num, 1)
            self.assertEqual(metadata.total_num_sessions, 1)
            self.assertEqual(metadata.words_spoken, 3)
            self.assertEqual(metadata.items_excluded, 0)
            self.assertEqual(metadata.percentile, 99)
            self.assertEqual(metadata.extra_categories, 0)
            self.assertEqual(metadata.revision, 0)
            self.assertEqual(','.join(metadata.languages), 'english,spanish')
            self.assertEqual(metadata.num_languages, 2)
            self.assertEqual(metadata.mcdi_type, 'test_mcdi_type')
            self.assertEqual(metadata.hard_of_hearing, constants.EXPLICIT_FALSE)
            self.assertEqual(metadata.deleted, constants.EXPLICIT_FALSE)

            contents = sorted(record.contents, key=lambda x: x.word)
            self.assertEqual(len(contents), 4)

            word_1_contents = contents[0]
            self.assertEqual(word_1_contents.word, 'word1')
            self.assertEqual(word_1_contents.value, 1)

            word_2_contents = contents[1]
            self.assertEqual(word_2_contents.word, 'word2')
            self.assertEqual(word_2_contents.value, 1)

            word_3_contents = contents[2]
            self.assertEqual(word_3_contents.word, 'word3')
            self.assertEqual(word_3_contents.value, 1)

            word_4_contents = contents[3]
            self.assertEqual(word_4_contents.word, 'word4')
            self.assertEqual(word_4_contents.value, 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_PARSE_DATABASE_ID
            )

        self.__setup_for_parse_with_percentile(callback)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_valid_not_provided_percentile(self):
        with unittest.mock.patch('prog_code.util.recalc_util.recalculate_percentile_raw') as mock:

            mock.return_value = 99

            def callback():
                self.__callback_called = True
                self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

                self.__test_automaton.process_column([
                    '1',
                    'test_child_id',
                    'test_study_id',
                    'test_study',
                    'm',
                    '24',
                    '2014/12/24',
                    '2016/12/24',
                    '1',
                    '1',
                    '3',
                    '0',
                    '',
                    '0',
                    '0',
                    'english,spanish',
                    '2',
                    'test_mcdi_type',
                    '0',
                    '0',
                    '1',
                    '1',
                    '1',
                    '0'
                ])

                records = self.__test_automaton.get_processed_records()
                self.assertEqual(len(records), 1)
                record = records[0]

                metadata = record.meta
                self.assertEqual(metadata.percentile, 99)

                mock.assert_called_with(
                    self.__adapter,
                    'test_mcdi_type',
                    constants.MALE,
                    3,
                    24
                )

            self.__setup_test_cdi(callback, False)
            self.assertTrue(self.__callback_called)

    def test_parse_full_record_valid_not_provided_age(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 1)
            record = records[0]

            metadata = record.meta
            self.assertTrue(abs(metadata.age - 24) < 0.1)

        self.__setup_for_parse_with_percentile(callback)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_valid_empty_num_languages(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 1)
            record = records[0]

            metadata = record.meta
            self.assertEqual(metadata.num_languages, 2)

        self.__setup_for_parse_with_percentile(callback)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_num_languages(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '3',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_word_value(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '2',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_word_type(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                'a',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_word_prefix(self):
        self.__callback_called = True
        def callback():
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '02',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_unexpected_words(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                ''
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_format(self):
        self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

        self.__test_automaton.process_column([
            '1',
            'test_child_id',
            'test_study_id',
            'test_study',
            'm',
            '24',
            '201/12/24',
            '2016/12/24',
            '1',
            '1',
            '3',
            '0',
            '99',
            '0',
            '0',
            'english,spanish',
            '2',
            'test_mcdi_type',
            '0',
            '0',
            '1',
            '1',
            '1',
            '0'
        ])

        records = self.__test_automaton.get_processed_records()
        self.assertEqual(len(records), 0)

        self.assertEqual(
            self.__test_automaton.get_state(),
            new_csv_import_util.STATE_FOUND_ERROR
        )

    def test_parse_full_record_invalid_provided_percentile(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '90',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_conflict_age(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '25.1',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_valid_not_provided_session_num(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '',
                '1',
                '3',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 1)
            record = records[0]

            metadata = record.meta
            self.assertEqual(metadata.session_num, 11)

        with unittest.mock.patch('prog_code.util.recalc_util.get_session_number') as mock:
            mock.return_value = 11

            self.__setup_for_parse_with_percentile(callback)

            mock.assert_called_with('test_study', 'test_study_id')

        self.assertTrue(self.__callback_called)

    def test_parse_full_record_valid_not_provided_num_words_spoken(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 1)
            record = records[0]

            metadata = record.meta
            self.assertEqual(metadata.words_spoken, 3)

        self.__setup_for_parse_with_percentile(callback)
        self.assertTrue(self.__callback_called)

    def test_parse_full_record_invalid_conflict_num_words_spoken(self):
        def callback():
            self.__callback_called = True
            self.__test_automaton.process_column(CORRECT_TEST_HEADER_VALUES)

            self.__test_automaton.process_column([
                '1',
                'test_child_id',
                'test_study_id',
                'test_study',
                'm',
                '24',
                '2014/12/24',
                '2016/12/24',
                '1',
                '1',
                '4',
                '0',
                '99',
                '0',
                '0',
                'english,spanish',
                '2',
                'test_mcdi_type',
                '0',
                '0',
                '1',
                '1',
                '1',
                '0'
            ])

            records = self.__test_automaton.get_processed_records()
            self.assertEqual(len(records), 0)

            self.assertEqual(
                self.__test_automaton.get_state(),
                new_csv_import_util.STATE_FOUND_ERROR
            )

        self.__setup_for_parse_with_percentile(callback, False)
        self.assertTrue(self.__callback_called)
