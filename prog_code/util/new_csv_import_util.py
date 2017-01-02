import csv
import collections
import datetime

import constants
import recalc_util

from ..struct import models

STATE_PARSE_HEADER = 0
STATE_PARSE_DATABASE_ID = 1
STATE_PARSE_CHILD_ID = 2
STATE_PARSE_STUDY_ID = 3
STATE_PARSE_STUDY = 4
STATE_PARSE_GENDER = 5
STATE_PARSE_AGE = 6
STATE_PARSE_BIRTHDAY = 7
STATE_PARSE_SESSION_DATE = 8
STATE_PARSE_SESSION_NUM = 9
STATE_PARSE_TOTAL_NUM_SESSIONS = 10
STATE_PARSE_WORDS_SPOKEN = 11
STATE_PARSE_ITEMS_EXCLUDED = 12
STATE_PARSE_PERCENTILE = 13
STATE_PARSE_EXTRA_CATEGORIES = 14
STATE_PARSE_REVISION = 15
STATE_PARSE_LANGUAGES = 16
STATE_PARSE_NUM_LANGUAGES = 17
STATE_PARSE_MCDI_TYPE = 18
STATE_PARSE_HARD_OF_HEARING = 19
STATE_PARSE_DELETED = 20
STATE_PARSE_START_WORDS = 21
STATE_PARSE_WORDS = 22
STATE_FOUND_ERROR = 23

EXPECTED_HEADER_FIELDS = [
    "child id",
    "study id",
    "study",
    "gender",
    "age",
    "birthday",
    "session date",
    "session num",
    "total num sessions",
    "words spoken",
    "items excluded",
    "percentile",
    "extra categories",
    "revision",
    "languages",
    "num languages",
    "mcdi type",
    "hard of hearing",
    "deleted"
]

EXPECTED_GENDER_VALUES = {
    "m": constants.MALE,
    "male": constants.MALE,
    "f": constants.FEMALE,
    "female": constants.FEMALE,
    "o": constants.OTHER_GENDER,
    "other": constants.OTHER_GENDER
}

EXPECTED_BOOLEAN_VALUES = {
    "y": constants.EXPLICIT_TRUE,
    "n": constants.EXPLICIT_FALSE,
    "yes": constants.EXPLICIT_TRUE,
    "no": constants.EXPLICIT_FALSE,
    "1": constants.EXPLICIT_TRUE,
    "0": constants.EXPLICIT_FALSE,
    str(constants.EXPLICIT_TRUE): constants.EXPLICIT_TRUE,
    str(constants.EXPLICIT_FALSE): constants.EXPLICIT_FALSE
}

ERROR_INVALID_LENGTH = "Expected atleast 19 rows in the provided dataset. Found %d rows."
ERROR_HEADER_UNEXPECTED_VALUE = "Expected header column value %s but got %s in row %d."
ERROR_NO_CHILD_ID = "Child ID was missing for record in column %d."
ERROR_NO_STUDY_ID = "Study ID was missing for record in column %d."
ERROR_NO_STUDY = "Study was missing for record in column %d."
ERROR_NO_GENDER = "Gender was missing for record in column %d."
ERROR_INVALID_GENDER = "An invalid value (%s) was provided for gender in column %d."
ERROR_UNEXPECTED_AGE_VALUE = "An invalid value (%s) was provided for age in column %d."
ERROR_NO_BIRTHDAY = "Birth date was missing for record in column %d."
ERROR_UNEXPECTED_BIRTHDAY_VALUE = "An invalid value (%s) was provided for birthday in column %d."
ERROR_NO_SESSION_DATE = "Session date was missing for record in column %d."
ERROR_UNEXPECTED_SESSION_DATE_VALUE = "An invalid value (%s) was provided for session date in column %d."
ERROR_NO_SESSION_NUM = "Session number as missing for record in column %d."
ERROR_UNEXPECTED_SESSION_NUM_VALUE = "An invalid value (%s) was provided for session number in column %d."
ERROR_NO_NUM_SESSIONS = "Number of sessions missing for record in column %d."
ERROR_NO_TOTAL_SESSIONS = "Total number of sessions was missing for column %d."
ERROR_UNEXPECTED_TOTAL_SESSIONS_VALUE = "An invalid value (%s) was provided for total sessions in column %d."
ERROR_UNEXPECTED_WORDS_SPOKEN = "An invalid value (%s) was provided for num words spoken in column %d."
ERROR_UNEXPECTED_EXCLUDED_ITEMS = "An invalid value (%s) was provided for num words excluded in column %d."
ERROR_UNEXPECTED_PERCENTILE = "An invalid value (%s) was provided for percentile in column %d."
ERROR_UNEXPECTED_EXTRA_CATEGORIES = "An invalid value (%s) was provided for extra categories in column %d."
ERROR_UNEXPECTED_REVISION = "An invalid value (%s) was provided for revision in column %d."
ERROR_NO_LANGUAGES = "Languages missing in column %d."
ERROR_UNEXPECTED_NUM_LANGUAGES = "An invalid value (%s) was provided for num languages in column %d."
ERROR_UNKNOWN_CDI_TYPE = "An unknown CDI type (%s) was encountered in column %d."
ERROR_WORDS_NOT_EXPECTED = "The words provided were not expected for CDI type %s (%s)."
ERROR_HARD_OF_HEARING_VALUE = "Unexpected value (%s) for hard of hearing in column %d."
ERROR_DELETED_VALUE = "Unexpected value (%s) for deleted in column %d."
ERROR_UNKNOWN_WORD_VAL = "Unexpected value (%s) for word %s in column %d."
ERROR_UNEXPECTED_WORD = "Too may word values found for column %d."
ERROR_INVALID_NUM_LANGUAGES = "Incorrect number of languages provided on column %d."
ERROR_INVALID_PERCENTILE = "Incorrect percentile provided on column %d (given %.1f but found %.1f)."
ERROR_INVALID_AGE = "Incorrect age on column %d (given %.1f but found %.1f)."
ERROR_INVALID_NUM_WORDS = "Incorrect num words on column %d (given %d but found %d)."


AutomatonResults = collections.namedtuple(
    "AutomatonResults",
    ["meta", "contents"]
)


CSVResults = collections.namedtuple(
    "CSVResults",
    ["records", "had_error", "error_msg"]
)


class UploadParserAutomaton:

    def __init__(self, cached_adapter):
        self.__cached_adapter = cached_adapter

        self.__state = STATE_PARSE_HEADER
        self.__error = None

        self.__columns_processed = 0
        self.__has_database_id = None
        self.__expected_words = None

        self.__child_id = None
        self.__study_id = None
        self.__study = None
        self.__gender = None
        self.__age = None
        self.__age_deferred = None
        self.__birthday = None
        self.__session_date = None
        self.__session_num = None
        self.__session_num_deferred = None
        self.__total_num_sessions = None
        self.__num_words_spoken = None
        self.__num_words_spoken_deferred = None
        self.__excluded_items = None
        self.__percentile_deferred = None
        self.__percentile = None
        self.__extra_categories = None
        self.__revision = None
        self.__languages = None
        self.__num_languages_deferred = None
        self.__num_languages = None
        self.__cdi_name = None
        self.__hard_of_hearing = None
        self.__deleted = None

        self.__expected_word_queue = None
        self.__allowed_word_values = None
        self.__count_as_spoken_values = None
        self.__word_values = None

        self.__processed_records = []

        self.__step_handlers = {
            STATE_PARSE_HEADER: lambda x: self.parse_header(x),
            STATE_PARSE_DATABASE_ID: lambda x: self.parse_database_id(x),
            STATE_PARSE_CHILD_ID: lambda x: self.parse_child_id(x),
            STATE_PARSE_STUDY_ID: lambda x: self.parse_study_id(x),
            STATE_PARSE_STUDY: lambda x: self.parse_study(x),
            STATE_PARSE_GENDER: lambda x: self.parse_gender(x),
            STATE_PARSE_AGE: lambda x: self.parse_age(x),
            STATE_PARSE_BIRTHDAY: lambda x: self.parse_birthday(x),
            STATE_PARSE_SESSION_DATE: lambda x: self.parse_session_date(x),
            STATE_PARSE_SESSION_NUM: lambda x: self.parse_session_num(x),
            STATE_PARSE_TOTAL_NUM_SESSIONS: lambda x: self.parse_total_num_sessions(x),
            STATE_PARSE_WORDS_SPOKEN: lambda x: self.parse_spoken_words(x),
            STATE_PARSE_ITEMS_EXCLUDED: lambda x: self.parse_excluded_items(x),
            STATE_PARSE_PERCENTILE: lambda x: self.parse_percentile(x),
            STATE_PARSE_EXTRA_CATEGORIES: lambda x: self.parse_extra_categories(x),
            STATE_PARSE_REVISION: lambda x: self.parse_revision(x),
            STATE_PARSE_LANGUAGES: lambda x: self.parse_languages(x),
            STATE_PARSE_NUM_LANGUAGES: lambda x: self.parse_num_languages(x),
            STATE_PARSE_MCDI_TYPE: lambda x: self.parse_cdi_type(x),
            STATE_PARSE_HARD_OF_HEARING: lambda x: self.parse_hard_of_hearing(x),
            STATE_PARSE_DELETED: lambda x: self.parse_deleted(x),
            STATE_PARSE_START_WORDS: lambda x: self.parse_word_start(x),
            STATE_PARSE_WORDS: lambda x: self.parse_word(x),
            STATE_FOUND_ERROR: lambda x: self.maintain_error_state(x)
        }

    def get_processed_records(self):
        return self.__processed_records

    def process_column(self, input_vals):
        if self.is_in_error():
            return
        
        if self.waiting_for_header():
            self.parse_header(input_vals)
        else:
            self.__process_non_header_col(input_vals)

    def __process_non_header_col(self, input_vals):
        for input_val in input_vals:
            
            if not self.__state in self.__step_handlers:
                self.enter_error_state("Automaton reached unexpected state.")
                self.__columns_processed += 1
                return

            step_handler = self.__step_handlers[self.__state]
            step_handler(input_val)

        self.__columns_processed += 1

        if self.is_in_error():
            return

        metadata = self.__create_metadata()
        words = self.__create_words()

        # Check calculated values
        if not self.__num_languages_deferred:
            user_provided_num_languages = metadata.num_languages
            expected_num_languages = len(self.__languages)

            if user_provided_num_languages != expected_num_languages:
                self.enter_error_state(
                    ERROR_INVALID_NUM_LANGUAGES % (self.__columns_processed + 1)
                )
                return

        if not self.__age_deferred:
            user_provided_age = metadata.age
            expected_age = self.__calculate_age()

            if abs(user_provided_age - expected_age) > 1:
                self.enter_error_state(
                    ERROR_INVALID_AGE % (
                        self.__columns_processed + 1,
                        user_provided_age,
                        expected_age
                    )
                )
                return

        if not self.__num_words_spoken_deferred:
            user_provided_num_words = metadata.words_spoken
            expected_num_words = self.__calculate_words_spoken()

            if user_provided_num_words != expected_num_words:
                self.enter_error_state(
                    ERROR_INVALID_NUM_WORDS % (
                        self.__columns_processed + 1,
                        user_provided_num_words,
                        expected_num_words
                    )
                )
                return

        if not self.__percentile_deferred:
            user_provided_percentile = metadata.percentile
            expected_percentile = self.__calculate_percentile()

            if abs(user_provided_percentile - expected_percentile) > 1:
                self.enter_error_state(
                    ERROR_INVALID_PERCENTILE % (
                        self.__columns_processed + 1,
                        user_provided_percentile,
                        expected_percentile
                    )
                )
                return

        self.__processed_records.append(AutomatonResults(metadata, words))

        if self.__has_database_id:
            self.__state = STATE_PARSE_DATABASE_ID
        else:
            self.__state = STATE_PARSE_CHILD_ID

    def __create_metadata(self):
        return models.SnapshotMetadata(
            None,
            self.__child_id,
            self.__study_id,
            self.__study,
            self.__gender,
            self.__get_age(),
            self.__birthday,
            self.__session_date,
            self.__get_session_num(),
            self.__total_num_sessions,
            self.__get_words_spoken(),
            self.__excluded_items,
            self.__get_percentile(),
            self.__extra_categories,
            self.__revision,
            self.__languages,
            self.__get_num_languages(),
            self.__cdi_name,
            self.__hard_of_hearing,
            self.__deleted
        )

    def __create_words(self):
        return map(
            lambda (word, value): models.SnapshotContent(None, word, value, 0),
            self.__word_values.items()
        )

    def __get_percentile(self):
        if self.__percentile_deferred:
            return self.__calculate_percentile()
        else:
            return self.__percentile

    def __calculate_percentile(self):
        return recalc_util.recalculate_percentile_raw(
            self.__cached_adapter,
            self.__cdi_name,
            self.__gender,
            self.__get_words_spoken(),
            self.__get_age()
        )

    def __get_words_spoken(self):
        if self.__num_words_spoken_deferred:
            return self.__calculate_words_spoken()
        else:
            return self.__num_words_spoken

    def __calculate_words_spoken(self):
        return len(filter(
            lambda x: x in self.__count_as_spoken_values,
            self.__word_values.values()
        ))

    def __get_age(self):
        if self.__age_deferred:
            return self.__calculate_age()
        else:
            return self.__age

    def __calculate_age(self):
        return recalc_util.recalculate_age_raw(
            self.__birthday,
            self.__session_date
        )

    def __get_num_languages(self):
        if self.__num_languages_deferred:
            return len(self.__languages)
        else:
            return self.__num_languages

    def __get_session_num(self):
        if self.__session_num_deferred:
            return recalc_util.get_session_number(
                self.__study,
                self.__study_id
            )
        else:
            return self.__session_num

    def waiting_for_header(self):
        return self.__state == STATE_PARSE_HEADER

    def is_in_error(self):
        return self.__state == STATE_FOUND_ERROR

    def get_state(self):
        return self.__state

    def get_error(self):
        return self.__error

    def expects_db_id_field(self):
        if self.__has_database_id is None:
            raise RuntimeError("Unset database ID row flag.")

        return self.__has_database_id

    def enter_error_state(self, error_message):
        if error_message is None:
            raise RuntimeError(
                "Unexpected automaton error message: " + error_message
            )

        self.__state = STATE_FOUND_ERROR
        self.__error = error_message

    def parse_header(self, header_column_cased):
        header_column = map(lambda x: x.lower(), header_column_cased)

        # Check minimum length
        if len(header_column) < 19:
            ERROR_INVALID_LENGTH % len(header_column)

        # Check for database ID
        self.__has_database_id = header_column[0] == "database id"

        # Parse metadata fields
        row_counter = self.__create_counter_continuation(
            1 if self.__has_database_id else 0
        )

        meta_checks = map(
            lambda x: self.__create_equality_check_continuation(x),
            EXPECTED_HEADER_FIELDS
        )

        meta_checks_successful = reduce(
            lambda last, next: next(last, row_counter(), header_column),
            meta_checks,
            True
        )

        if not meta_checks_successful:
            return

        # Parse remaining as words
        self.__expected_words = header_column[row_counter():]

        # Accept new state
        self.__prepare_for_new_record()

    def parse_database_id(self, input_val):
        self.__state = STATE_PARSE_CHILD_ID

    def parse_child_id(self, input_val):
        self.__child_id = None if self.__is_empty(input_val) else input_val
        self.__state = STATE_PARSE_STUDY_ID

    def parse_study_id(self, input_val):
        if self.__is_empty(input_val):
            msg = ERROR_NO_STUDY_ID % (self.__columns_processed + 1)
            self.enter_error_state(msg)
            return

        self.__study_id = input_val
        self.__state = STATE_PARSE_STUDY

    def parse_study(self, input_val):
        if self.__is_empty(input_val):
            msg = ERROR_NO_STUDY % (self.__columns_processed + 1)
            self.enter_error_state(msg)
            return

        self.__study = input_val
        self.__state = STATE_PARSE_GENDER

    def parse_gender(self, input_val_cased):
        input_val = input_val_cased.lower()

        col_number = self.__columns_processed + 1

        if self.__is_empty(input_val):
            msg = ERROR_NO_GENDER % (col_number)
            self.enter_error_state(msg)
            return

        if not input_val in EXPECTED_GENDER_VALUES:
            msg = ERROR_INVALID_GENDER % (input_val_cased, col_number)
            self.enter_error_state(msg)
            return

        self.__gender = EXPECTED_GENDER_VALUES[input_val]
        self.__state = STATE_PARSE_AGE

    def parse_age(self, input_val):
        if self.__is_empty(input_val):
            self.__age_deferred = True
            self.__state = STATE_PARSE_BIRTHDAY
            return
        else:
            self.__age_deferred = False

        candidate_age = self.__parse_float(input_val)

        if candidate_age == None or candidate_age <= 0:
            msg = ERROR_UNEXPECTED_AGE_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__state = STATE_PARSE_BIRTHDAY
        self.__age = candidate_age

    def parse_birthday(self, input_val):
        if self.__is_empty(input_val):
            msg = ERROR_NO_BIRTHDAY % (self.__columns_processed + 1)
            self.enter_error_state(msg)
            return

        candidate_date = self.__parse_date(input_val)
        if candidate_date == None:
            msg = ERROR_UNEXPECTED_BIRTHDAY_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__birthday = candidate_date
        self.__state = STATE_PARSE_SESSION_DATE

    def parse_session_date(self, input_val):
        if self.__is_empty(input_val):
            msg = ERROR_NO_SESSION_DATE % (self.__columns_processed + 1)
            self.enter_error_state(msg)
            return

        candidate_date = self.__parse_date(input_val)
        if candidate_date == None:
            msg = ERROR_UNEXPECTED_SESSION_DATE_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__session_date = candidate_date
        self.__state = STATE_PARSE_SESSION_NUM

    def parse_session_num(self, input_val):
        if self.__is_empty(input_val):
            self.__session_num_deferred = True
            self.__state = STATE_PARSE_TOTAL_NUM_SESSIONS
            return
        else:
            self.__session_num_deferred = False

        candidate_session_num = self.__parse_float(input_val)

        if candidate_session_num == None or candidate_session_num <= 0:
            msg = ERROR_UNEXPECTED_SESSION_NUM_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__state = STATE_PARSE_TOTAL_NUM_SESSIONS
        self.__session_num = candidate_session_num

    def parse_total_num_sessions(self, input_val):
        if self.__is_empty(input_val):
            msg = ERROR_NO_TOTAL_SESSIONS % (self.__columns_processed + 1)
            self.enter_error_state(msg)
            return

        candidate_num_sessions = self.__parse_int(input_val)
        if candidate_num_sessions == None or candidate_num_sessions <= 0:
            msg = ERROR_UNEXPECTED_TOTAL_SESSIONS_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__total_num_sessions = candidate_num_sessions
        self.__state = STATE_PARSE_WORDS_SPOKEN

    def parse_spoken_words(self, input_val):
        if self.__is_empty(input_val):
            self.__num_words_spoken_deferred = True
            self.__state = STATE_PARSE_ITEMS_EXCLUDED
            return
        else:
            self.__num_words_spoken_deferred = False

        candidate_words_spoken = self.__parse_int(input_val)
        if candidate_words_spoken == None or candidate_words_spoken < 0:
            msg = ERROR_UNEXPECTED_WORDS_SPOKEN % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__num_words_spoken = candidate_words_spoken
        self.__state = STATE_PARSE_ITEMS_EXCLUDED

    def parse_excluded_items(self, input_val):
        if self.__is_empty(input_val):
            candidate_excluded_items = 0
        else:
            candidate_excluded_items = self.__parse_int(input_val)
            value_missing = candidate_excluded_items == None
            if value_missing or candidate_excluded_items < 0:
                msg = ERROR_UNEXPECTED_EXCLUDED_ITEMS % (
                    input_val,
                    self.__columns_processed + 1
                )
                self.enter_error_state(msg)
                return

        self.__excluded_items = candidate_excluded_items
        self.__state = STATE_PARSE_PERCENTILE

    def parse_percentile(self, input_val):
        if self.__is_empty(input_val):
            self.__percentile_deferred = True
            self.__state = STATE_PARSE_EXTRA_CATEGORIES
            return
        else:
            self.__percentile_deferred = False

        percentile = self.__parse_float(input_val)
        if percentile == None or percentile < 0 or percentile > 100:
            msg = ERROR_UNEXPECTED_PERCENTILE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__percentile = percentile
        self.__state = STATE_PARSE_EXTRA_CATEGORIES

    def parse_extra_categories(self, input_val):
        if self.__is_empty(input_val):
            candidate_extra_categories = 0
        else:
            candidate_extra_categories = self.__parse_int(input_val)
            value_missing = candidate_extra_categories == None
            if value_missing or candidate_extra_categories < 0:
                msg = ERROR_UNEXPECTED_EXTRA_CATEGORIES % (
                    input_val,
                    self.__columns_processed + 1
                )
                self.enter_error_state(msg)
                return

        self.__extra_categories = candidate_extra_categories
        self.__state = STATE_PARSE_REVISION

    def parse_revision(self, input_val):
        if self.__is_empty(input_val):
            candidate_revision = 0
        else:
            candidate_revision = self.__parse_int(input_val)
            value_missing = candidate_revision == None
            if value_missing or candidate_revision < 0:
                msg = ERROR_UNEXPECTED_REVISION % (
                    input_val,
                    self.__columns_processed + 1
                )
                self.enter_error_state(msg)
                return

        self.__revision = candidate_revision
        self.__state = STATE_PARSE_LANGUAGES

    def parse_languages(self, input_val):
        if self.__is_empty(input_val):
            msg = ERROR_NO_LANGUAGES % (self.__columns_processed + 1)
            self.enter_error_state(msg)
            return

        self.__languages = map(lambda x: x.strip(), input_val.split(","))
        self.__state = STATE_PARSE_NUM_LANGUAGES

    def parse_num_languages(self, input_val):
        if self.__is_empty(input_val):
            self.__num_languages_deferred = True
            self.__state = STATE_PARSE_MCDI_TYPE
            return
        else:
            self.__num_languages_deferred = False

        num_languages = self.__parse_float(input_val)
        if num_languages == None or num_languages <= 0:
            msg = ERROR_UNEXPECTED_NUM_LANGUAGES % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__num_languages = num_languages
        self.__state = STATE_PARSE_MCDI_TYPE

    def parse_cdi_type(self, cdi_name):
        mcdi_model = self.__cached_adapter.load_mcdi_model(cdi_name)

        # Check CDI was known
        if mcdi_model == None:
            msg = ERROR_UNKNOWN_CDI_TYPE % (
                cdi_name,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        # Check words were present
        required_words = set(reduce(
            lambda last, cur: last + cur["words"],
            mcdi_model.details["categories"],
            []
        ))

        required_words = set(map(
            lambda x: x.replace("*", "").lower(),
            required_words
        ))

        # Check allowed values
        explicit_options = set(map(
            lambda x: x["value"],
            mcdi_model.details["options"]
        ))

        prefill_values = set(reduce(
            lambda prev, cur: extend_list(prev, cur.get("prefill_value", [])),
            mcdi_model.details["options"],
            []
        ))

        self.__allowed_word_values = explicit_options.union(prefill_values)

        self.__count_as_spoken_values = set(mcdi_model.details["count_as_spoken"])

        difference = required_words.symmetric_difference(self.__expected_words)
        if len(difference) > 0:
            diff_str = ",".join(difference)
            self.enter_error_state(
                ERROR_WORDS_NOT_EXPECTED % (cdi_name, diff_str)
            )
            return

        # Accept cdi model name
        self.__cdi_name = cdi_name
        self.__state = STATE_PARSE_HARD_OF_HEARING

    def parse_hard_of_hearing(self, input_val):
        if not input_val in EXPECTED_BOOLEAN_VALUES:
            msg = ERROR_HARD_OF_HEARING_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__hard_of_hearing = EXPECTED_BOOLEAN_VALUES[input_val]
        self.__state = STATE_PARSE_DELETED

    def parse_deleted(self, input_val):
        if not input_val in EXPECTED_BOOLEAN_VALUES:
            msg = ERROR_DELETED_VALUE % (
                input_val,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__deleted = EXPECTED_BOOLEAN_VALUES[input_val]
        self.__state = STATE_PARSE_START_WORDS

    def parse_word_start(self, input_val):
        self.__word_values = {}
        self.__expected_word_queue = collections.deque(self.__expected_words)

        self.__state = STATE_PARSE_WORDS
        self.parse_word(input_val)

    def parse_word(self, input_val):
        if len(self.__expected_word_queue) == 0:
            self.enter_error_state(
                ERROR_UNEXPECTED_WORD % (self.__columns_processed + 1)
            )
            return

        word = self.__expected_word_queue.popleft()

        input_val_int = self.__parse_int(input_val)
        input_given = input_val_int == None
        if input_given or not input_val_int in self.__allowed_word_values:
            msg = ERROR_UNKNOWN_WORD_VAL % (
                input_val,
                word,
                self.__columns_processed + 1
            )
            self.enter_error_state(msg)
            return

        self.__word_values[word] = input_val_int

    def maintain_error_state(self, input_val):
        pass

    def __create_equality_check_continuation(self, expected):

        def check(last_successful, i, header_col):
            if not last_successful:
                return False
            elif header_col[i] == expected:
                return True
            else:
                msg = ERROR_HEADER_UNEXPECTED_VALUE % (
                    expected,
                    header_col[i],
                    i + 1
                )
                self.enter_error_state(msg)
                return False

        return check

    def __create_counter_continuation(self, start_num):
        counter = Counter(start_num)

        return lambda: counter.return_and_increment()

    def __prepare_for_new_record(self):
        self.__columns_processed += 1

        if self.__has_database_id:
            self.__state = STATE_PARSE_DATABASE_ID
        else:
            self.__state = STATE_PARSE_CHILD_ID

    def __is_empty(self, candidate):
        return candidate.strip() == ""

    def __parse_float(self, str_val):
        str_val = str_val.strip()

        if str_val == "0":
            return 0

        invalid_zero = str_val.startswith("0") and not str_val.startswith("0.")
        if invalid_zero or self.__is_empty(str_val):
            return None

        try:
            return float(str_val)
        except ValueError:
            return None

    def __parse_int(self, str_val):
        str_val = str_val.strip()

        if str_val == "0":
            return 0

        if str_val.startswith("0") or self.__is_empty(str_val):
            return None

        try:
            return int(str_val)
        except ValueError:
            return None

    def __parse_date(self, str_val):
        str_val = str_val.strip().replace("-", "/")

        converted_date = self.__parse_date_iso(str_val)
        if not converted_date:
            converted_date = self.__parse_date_usa(str_val)

        if not converted_date:
            return None

        return converted_date.date().isoformat().replace("-", "/")

    def __parse_date_iso(self, str_val):
        try:
            return datetime.datetime.strptime(str_val, "%Y/%m/%d")
        except ValueError:
            return None

    def __parse_date_usa(self, str_val):
        try:
            return datetime.datetime.strptime(str_val, "%m/%d/%Y")
        except ValueError:
            return None


class Counter:

    def __init__(self, start_num):
        self.__i = start_num

    def return_and_increment(self):
        old_val = self.__i
        self.__i += 1
        return old_val


def process_csv(input_rows_iterator):
    columns = []

    input_rows = list(csv.reader(input_rows_iterator))

    for col_num in range(0, len(input_rows[0])):
        column = map(lambda row: row[col_num], input_rows)
        columns.append(column)

    automaton = UploadParserAutomaton(recalc_util.CachedMCDIAdapter())

    for column in columns:
        automaton.process_column(column)

    return CSVResults(
        automaton.get_processed_records(),
        automaton.is_in_error(),
        automaton.get_error()
    )


def extend_list(prev, cur):
    cur = cur if is_iterable(cur) else [cur]
    return prev + cur


def is_iterable(target):
    try:
        iter(target)
        return True
    except TypeError:
        return False

