"""Utility to import a CSV file into the lab database.

@author: Sam Pottinger
@license: GNU GPL v3
"""

STATE_PARSE_CHILD_DB_ID = 0
STATE_PARSE_CHILD_STUDY_ID = 1
STATE_PARSE_STUDY_AND_SOURCE = 2
STATE_PARSE_GENDER = 3
STATE_PARSE_AGE = 4
STATE_PARSE_DATE_OF_BIRTH = 5
STATE_PARSE_DATE_OF_SESSION = 6
STATE_PARSE_SESSION_NUM = 7
STATE_PARSE_TOTAL_SESSION_NUM = 8
STATE_PARSE_WORDS_SPOKEN = 9
STATE_PARSE_ITEMS_EXCLUDED = 10
STATE_PARSE_PERCENTILE = 11
STATE_PARSE_EXTRA_CATEGORIES = 12
STATE_PARSE_SECTION_WORD_HEADING = 13
STATE_PARSE_WORDS = 14
STATE_FOUND_ERROR = 15

FAILED_SANITY_CHECK_ERR = 'Expected \"%s\" on row %d but found \"%s\".'
GENDER_INVALID_ERR = 'Expected M (male), F (female), or O (other) but found '\
    '%s on row %d'
INT_EXPECTED_ERR = 'Was expecting an integer but found \"%s\" on row %d.'
FLOAT_EXPECTED_ERR = 'Was expecting a number but found \"%s\" on row %d.'
EXTRA_CAT_INVALID_ERR = 'Expected Y or N but found \"%s\" on row %d.'
DATE_EXPECTED_ERR = 'Was expecting a date but found \"%s\" on row %d.'
DATE_MALFORMED_ERR = 'Found a date (%s) but was expecting form MM/DD/YYYY on '\
    'row %d.'
INVALID_PERCENT_ERR = 'Invalid percent (%s) found on row %d.'
INVALID_WORD_VAL_ERROR = 'Invalid word value (%s) found on row %d.'

import csv
import cStringIO as stringIO
import datetime

from ..struct import models

import constants
import db_util
import math_util


class UploadParserAutomaton:
    """Automaton which processes CSV files to import into the lab database."""

    def __init__(self, percentile_table=None, state=STATE_PARSE_CHILD_DB_ID):
        """Create a new upload parser automaton.

        @keyword percentile_table: The raw percentile tables to use
            while calculating children percentiles.
        @type percentile_table: 2D float array
        """
        self.__percentile_table = percentile_table
        self.__needing_percentiles = []
        self.__state_matrix = {
            STATE_PARSE_CHILD_DB_ID: self.parse_child_db_id,
            STATE_PARSE_CHILD_STUDY_ID: self.parse_child_study_id,
            STATE_PARSE_STUDY_AND_SOURCE: self.parse_study_and_source,
            STATE_PARSE_GENDER: self.parse_gender,
            STATE_PARSE_AGE: self.parse_age,
            STATE_PARSE_DATE_OF_BIRTH: self.parse_date_of_birth,
            STATE_PARSE_DATE_OF_SESSION: self.parse_date_of_session,
            STATE_PARSE_SESSION_NUM: self.parse_session_num,
            STATE_PARSE_TOTAL_SESSION_NUM: self.parse_total_session_num,
            STATE_PARSE_WORDS_SPOKEN: self.parse_words_spoken,
            STATE_PARSE_ITEMS_EXCLUDED: self.parse_items_excluded,
            STATE_PARSE_PERCENTILE: self.parse_percentile,
            STATE_PARSE_EXTRA_CATEGORIES: self.parse_extra_categories,
            STATE_PARSE_SECTION_WORD_HEADING: self.parse_section_word_heading,
            STATE_PARSE_WORDS: self.parse_words,
            STATE_FOUND_ERROR: self.handle_found_error
        }
        self.__state = state
        self.__error = None
        self.__prototypes = []

    def enter_error_state(self, message):
        self.__state = STATE_FOUND_ERROR
        self.__error = message

    def sanity_check(self, step_val, expected, row_num):
        if step_val[1] == expected:
            return True
        else:
            msg = FAILED_SANITY_CHECK_ERR % (expected, row_num, step_val[1])
            self.enter_error_state(msg)
            return False

    def safe_parse_float(self, target_val, row_num):
        try:
            return float(target_val)
        except ValueError:
            self.enter_error_state(FLOAT_EXPECTED_ERR % (target_val, row_num))
            return None

    def safe_parse_int(self, target_val, row_num):
        try:
            return int(target_val)
        except ValueError:
            self.enter_error_state(INT_EXPECTED_ERR % (target_val, row_num))
            return None

    def safe_parse_date(self, target_val, row_num):
        parts = target_val.split('/')
        if len(parts) != 3:
            self.enter_error_state(DATE_EXPECTED_ERR % (target_val, row_num))
            return

        try:
            month = int(parts[0])
            day = int(parts[1])
            year = int(parts[2])
        except ValueError:
            self.enter_error_state(DATE_MALFORMED_ERR % (target_val, row_num))
            return None

        invalid_date = year < 1000
        invalid_date = invalid_date or month < 0 or month > 12
        invalid_date = invalid_date or day > 31 or day < 0
        if invalid_date:
            self.enter_error_state(DATE_MALFORMED_ERR % (target_val, row_num))
            return None

        return '%d/%d/%d' % (year, month, day)

    def step(self, step_val, row_num):
        for i in range(0, len(step_val)):
            step_val[i] = step_val[i].strip()
        self.__state_matrix[self.__state](step_val, row_num)

    def parse_child_db_id(self, step_val, row_num):
        passed_sanity_check = self.sanity_check(
            step_val,
            'Child\'s ID (from database)',
            row_num
        )

        if not passed_sanity_check:
            return
        
        for val in step_val[2:]:
            converted_val = self.safe_parse_int(val, row_num)
            if converted_val == None: return
            else: self.__prototypes.append({ 'child_id': converted_val })

        self.__state += 1

    def parse_child_study_id(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Name / Number', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            prototype['study_id'] = val

        self.__state += 1

    def parse_study_and_source(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Study / Source', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            prototype['study'] = val

        self.__state += 1

    def parse_gender(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Gender', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = None

            if val == 'M': converted_val = constants.MALE
            elif val == 'F': converted_val = constants.FEMALE
            elif val == 'O': converted_val = constants.OTHER_GENDER
            else:
                self.enter_error_state(GENDER_INVALID_ERR % (val, row_num))
                return

            prototype['gender'] = converted_val

        self.__state += 1

    def parse_age(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Age (months)', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_float(val, row_num)
            if converted_val == None: return
            else: prototype['age'] = converted_val

        self.__state += 1

    def parse_date_of_birth(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Date of Birth', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_date(val, row_num)
            if converted_val == None: return
            else: prototype['birthday'] = converted_val

        self.__state += 1

    def parse_date_of_session(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Date of Session', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_date(val, row_num)
            if converted_val == None: return
            else: prototype['session_date'] = converted_val

        self.__state += 1

    def parse_session_num(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Session #', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_int(val, row_num)
            if converted_val == None: return
            else: prototype['session_num'] = converted_val

        self.__state += 1

    def parse_total_session_num(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Total # of Sessions', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_int(val, row_num)
            if converted_val == None: return
            else: prototype['total_num_sessions'] = converted_val

        self.__state += 1

    def parse_words_spoken(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Words Spoken', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_int(val, row_num)
            if converted_val == None: return
            else: prototype['words_spoken'] = converted_val

        self.__state += 1

    def parse_items_excluded(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Items Excluded', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = self.safe_parse_int(val, row_num)
            if converted_val == None: return
            else: prototype['items_excluded'] = converted_val

        self.__state += 1

    def parse_percentile(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Percentile', row_num):
            return

        index = 0
        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            if val == 'calculate':
                self.__needing_percentiles.append(index)
                prototype['percentile'] = -1
            else:
                converted_val = self.safe_parse_float(val, row_num)
                if converted_val == None:
                    self.enter_error_state(
                        INVALID_PERCENT_ERR % (converted_val, row_num),
                    )
                    return
                elif converted_val < 0 or converted_val > 100:
                    self.enter_error_state(
                        INVALID_PERCENT_ERR % (converted_val, row_num),
                    )
                    return
                else:
                    prototype['percentile'] = converted_val
            index += 1

        self.__state += 1

    def parse_extra_categories(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Extra Categories?', row_num):
            return

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            converted_val = None

            if val == 'N': converted_val = constants.EXPLICIT_FALSE
            elif val == 'Y': converted_val = constants.EXPLICIT_TRUE
            else:
                self.enter_error_state(EXTRA_CAT_INVALID_ERR % (val, row_num))
                return

            prototype['extra_categories'] = converted_val

        self.__state += 1

    def parse_section_word_heading(self, step_val, row_num):
        if not self.sanity_check(step_val, 'Word', row_num): return
        else: self.__state += 1

        for prototype in self.__prototypes:
            prototype['words'] = []

    def parse_words(self, step_val, row_num):
        word = step_val[1]

        for (val, prototype) in zip(step_val[2:], self.__prototypes):
            
            converted_val = None
            if val == 'na':
                converted_val = constants.NO_DATA
            elif val == 'y':
                converted_val = constants.EXPLICIT_TRUE
            elif val == 'n':
                converted_val = constants.EXPLICIT_FALSE
            else:
                try:
                    converted_val = int(val)
                except ValueError:
                    converted_val = None
            
            if converted_val == None:
                self.enter_error_state(
                    INVALID_WORD_VAL_ERROR % (step_val, row_num)
                )
                return
            else:
                prototype['words'].append({
                    'word': word,
                    'val': converted_val
                })

    def finish(self):
        if self.__state == STATE_FOUND_ERROR:
            return

        for child_index in self.get_list_needing_precentile():
            target_prototype = self.__prototypes[child_index]
            known_words = filter(
                lambda x: x['val'] == constants.EXPLICIT_TRUE,
                target_prototype['words']
            )
            all_words = filter(
                lambda x: x['val'] != constants.NO_DATA,
                target_prototype['words']
            )

            known_words_count = len(known_words)
            all_words_count = len(all_words)
            percentile = math_util.find_percentile(
                self.__percentile_table[target_prototype['gender']].details,
                known_words_count,
                target_prototype['age'],
                all_words_count
            )

            target_prototype['percentile'] = percentile

    def handle_found_error(self, step_val, row_num):
        pass

    def get_state(self):
        return self.__state

    def set_state(self, new_state):
        self.__state = new_state

    def get_error(self):
        return self.__error

    def get_prototypes(self):
        return self.__prototypes

    def get_list_needing_precentile(self):
        return self.__needing_percentiles

    def set_prototypes(self, prototypes):
        self.__prototypes = prototypes


def parse_csv_prototypes(contents, percentile_table, act_as_file=False):
    if act_as_file:
        targetBuffer = contents
    else:
        targetBuffer = stringIO.StringIO(contents)
    
    reader = csv.reader(targetBuffer)

    automaton = UploadParserAutomaton(percentile_table)
    row_num = 1
    for row in reader:
        automaton.step(row, row_num)
        row_num += 1

    if automaton.get_state() != STATE_FOUND_ERROR:
        automaton.finish()

    return {
        'error': automaton.get_error(),
        'prototypes': automaton.get_prototypes()
    }


def build_snapshot(prototype, mcdi_type, languages, hard_of_hearing, cursor):
    metadata = models.SnapshotMetadata(
        -1,
        prototype['child_id'],
        prototype['study_id'],
        prototype['study'],
        prototype['gender'],
        prototype['age'],
        prototype['birthday'],
        prototype['session_date'],
        prototype['session_num'],
        prototype['total_num_sessions'],
        prototype['words_spoken'],
        prototype['items_excluded'],
        prototype['percentile'],
        prototype['extra_categories'],
        0,
        languages,
        len(languages),
        mcdi_type,
        hard_of_hearing,
        0
    )

    words = {}
    for word_prototype in prototype['words']:
        words[word_prototype['word']] = word_prototype['val']

    db_util.insert_snapshot(metadata, words, cursor)
    return metadata


def parse_csv(contents, mcdi_type, languages, hard_of_hearing,
    act_as_file=False):

    mcdi_model = db_util.load_mcdi_model(mcdi_type)
    percentile_names = mcdi_model.details['percentiles']
    
    male_percentiles_name = percentile_names['male']
    female_percentiles_name = percentile_names['female']
    other_percentiles_name = percentile_names['other']

    male_percentiles = db_util.load_percentile_model(male_percentiles_name)
    female_percentiles = db_util.load_percentile_model(female_percentiles_name)
    other_percentiles = db_util.load_percentile_model(other_percentiles_name)
    
    percentile_tables = {
        constants.MALE: male_percentiles,
        constants.FEMALE: female_percentiles,
        constants.OTHER_GENDER: other_percentiles
    }

    connection = db_util.get_db_connection()
    cursor = connection.cursor()

    parse_info = parse_csv_prototypes(contents, percentile_tables, act_as_file)
    if parse_info['error']:
        connection.commit()
        connection.close()
        return {'error': parse_info['error']}

    prototypes = parse_info['prototypes']
    for prototype in prototypes:
        build_snapshot(prototype, mcdi_type, languages, hard_of_hearing, cursor)

    connection.commit()
    connection.close()
    return {'error': None}
