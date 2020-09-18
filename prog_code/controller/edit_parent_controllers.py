"""Logic for managing parent accounts and parent CDI forms.

Loginc for managing parent accounts, sending parent CDI forms, and processing
CDI parent form responses.

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

@author: Sam Pottinger
@license: GNU GPL v3
"""
import datetime
import typing

import dateutil.parser as dateutil_parser
import flask

from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import math_util
from ..util import parent_account_util
from ..util import recalc_util
from ..util import session_util
from ..util import user_util
from ..util import type_util

from ..struct import models

from . import controller_types

from cdibase import app

VALID_GENDER_VALUES = [constants.MALE, constants.FEMALE, constants.OTHER_GENDER]

CDI_TYPE_NOT_GIVEN_MSG = 'CDI type required.'
PARENT_EMAIL_NOT_GIVEN_MSG = 'Provided parent email appears not to be a ' \
    'valid email address.'
PARENT_FORM_SENT_MSG = 'CDI form sent.'
NO_ID_MSG = 'Must provide an integer global ID or both a study ID and study ' \
    'name.'
GLOBAL_ID_MUST_BE_INT_MSG = 'The global database ID for a child must be an ' \
    'integer.'
GENDER_INVALID_MSG = 'The provided gender for this child was not recognized.'
DATE_OUT_STR = '%Y/%m/%d'
DATE_INVALID_MSG = '%s is not a valid date.'
INVALID_ITEMS_EXCLUDED_MSG = 'Invalid items count.'
INVALID_TOTAL_SESS_MSG = 'Invalid total sessions count.'
INVALID_EXTRA_CATEGORIES_MSG = 'Extra categories invalid.'
LANGUAGES_NOT_PROVIDED_MSG = 'Languages list not provided.'
COULD_NOT_FIND_PERCENTILES_MSG = 'Could not find percentile information.'
SUBMITTED_MSG = 'Form submitted to the lab.'
PARENT_ACCOUNT_CONTROLS_URL = '/base/parent_accounts'
WORD_RESPONSE_ID_TEMPL = '%s_report'
BIRTHDAY_INVALID_MSG = 'Birthday invalid: %s'
WORD_VALUE_MISSING_MSG = 'Whoops! You seemed to have forgotten to provide a '\
    'value for %s.'
WORD_VALUE_INVALID_MSG = 'Whoops! You seemed to have forgotten to provide a '\
    'value for %s.'
NO_GLOBAL_ID_MSG = 'No global ID specified.'
THANK_YOU_MSG_URL = '/base/parent_cdi/_thanks'


def is_none_or_negative(target: typing.Optional[float]) -> bool:
    """Determine if the given value is none or negative, making it invalid for some fields.

    @param target: The value to test.
    @returns: True if none or negative. False otherwise.
    """
    return target == None or target < 0 # type: ignore


@app.route('/base/parent_accounts', methods=['GET', 'POST'])
@session_util.require_login(edit_parents=True)
def send_cdi_form() -> controller_types.ValidFlaskReturnTypes:
    """Create and send a parent CDI form.

    Controller that, on GET, displays controls to send CDI parent forms by
    email and, on POST, actually sends those emails by coordinating various
    utility modules.

    @return: HTML page for creating parent forms if a GET request. Redirect
        if POST. Session confirmation and error messages will be set by this
        handler.
    @rtype: Flask response.
    """
    request = flask.request
    if request.method == 'POST':

        # Read user provided values
        form_id: str = parent_account_util.generate_unique_cdi_form_id() # type: ignore
        global_id_str: str = request.form.get('global_id') # type: ignore
        gender: str = request.form.get('gender') # type: ignore
        items_excluded: str = request.form.get('items_excluded') # type: ignore
        total_num_sessions: str = request.form.get('total_num_sessions') # type: ignore
        extra_categories: str = request.form.get('extra_categories') # type: ignore
        study_id: str = request.form.get('study_id') # type: ignore
        study: str = request.form.get('study') # type: ignore
        birthday: str = request.form.get('birthday') # type: ignore
        languages: str = request.form.get('languages') # type: ignore
        hard_of_hearing_str: str = request.form.get('hard_of_hearing', False) # type: ignore
        hard_of_hearing = hard_of_hearing_str == constants.FORM_SELECTED_VALUE
        child_name: str = request.form.get('child_name') # type: ignore
        parent_email: str = request.form.get('parent_email') # type: ignore
        cdi_type: str = request.form.get('cdi_type') # type: ignore

        # Save for future send
        flask.session['LAST_PARENT_PARAMS'] = {
            'global_id': global_id_str,
            'gender': gender,
            'items_excluded': items_excluded,
            'total_num_sessions': total_num_sessions,
            'extra_categories': extra_categories,
            'study_id': study_id,
            'study': study,
            'birthday': birthday,
            'languages': languages,
            'hard_of_hearing': hard_of_hearing,
            'child_name': child_name,
            'parent_email': parent_email,
            'cdi_type': cdi_type
        }

        # Check that the CDI type provided has been defined and can be found
        # in the application database.
        cdi_model_maybe = db_util.load_cdi_model(cdi_type)
        if cdi_type == None or cdi_type == '' or cdi_model_maybe == None:
            flask.session[constants.ERROR_ATTR] = CDI_TYPE_NOT_GIVEN_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        cdi_model: models.CDIFormat = cdi_model_maybe # type: ignore

        # Ensure either a global child ID was provided or that both a global
        # and study ID are available.
        missing_global_id = global_id_str == None or global_id_str == ''
        missing_study_id = study_id == None or study_id == ''
        missing_study = study == None or study == ''
        if missing_global_id and (missing_study_id or missing_study):
            flask.session[constants.ERROR_ATTR] = NO_ID_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Ensure that the email address provided at least has the form of an
        # email address. Note that, due to the asynchronous nature of email,
        # there is not currently a method for reporting failed delivery of
        # emails.
        if not parent_account_util.is_likely_email_address(parent_email):
            flask.session[constants.ERROR_ATTR] = PARENT_EMAIL_NOT_GIVEN_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Ensure that, if a birthday value for this child was provided, that the
        # birthday was provided in the correct format.
        if birthday != None and birthday != '':
            if not parent_account_util.is_birthday_valid(birthday):
                msg = DATE_INVALID_MSG % birthday
                flask.session[constants.ERROR_ATTR] = msg,
                return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)
            birthday_date = dateutil_parser.parse(
                birthday,
                dayfirst=False,
                yearfirst=False
            )
            birthday = birthday_date.strftime(DATE_OUT_STR)

        # Use the specified interpretation / presentation formation to parse the
        # provided hard of hearing status.
        hard_of_hearing_int: typing.Optional[int] = None
        if hard_of_hearing != None and hard_of_hearing != '':
            if hard_of_hearing:
                hard_of_hearing_int = constants.EXPLICIT_TRUE
            else:
                hard_of_hearing_int = constants.EXPLICIT_FALSE

        # Parse out parent form attributes that are integers.
        items_excluded_int = interp_util.safe_int_interpret(items_excluded)
        extra_categories_int = interp_util.safe_int_interpret(extra_categories)
        total_num_sessions_int = interp_util.safe_int_interpret(total_num_sessions)

        # Ensure languages are provided or try to get it from prior
        languages_str: typing.Optional[str] = None
        num_languages: typing.Optional[int] = None

        if languages != None and languages != '':
            languages_list = languages.split(',')
            languages_str = ','.join(languages_list)
            num_languages = len(languages_list)

        # Ensure gender information specified and, if it is, make sure the
        # provided gender value is valid.
        gender_int: typing.Optional[int] = None
        gender_int = interp_util.safe_int_interpret(gender)

        has_gender_info = gender != '' and gender != None
        if has_gender_info and not gender_int in VALID_GENDER_VALUES:
            flask.session[constants.ERROR_ATTR] = GENDER_INVALID_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Create a new parent form model but wait to save it until resolving
        # missing values by using a previous entry for the specified child.
        new_form = models.ParentForm(
            form_id,
            child_name,
            parent_email,
            cdi_type,
            global_id_str,
            study_id,
            study,
            gender_int,
            birthday,
            items_excluded_int,
            extra_categories_int,
            languages_str,
            num_languages,
            hard_of_hearing_int,
            total_num_sessions_int
        )

        # If a parent form model is missing information about a child, load the
        # rest of the missing information from a previous CDI snapshot for the
        # child.
        resolver = parent_account_util.AttributeResolutionResolver()
        resolver.fill_parent_form_defaults(new_form)

        # Ensure language information was in fact loaded or provided
        if new_form.languages == None or new_form.languages == '':
            flask.session[constants.ERROR_ATTR] = LANGUAGES_NOT_PROVIDED_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Ensure gender information was in fact loaded or provided
        if new_form.gender == None or new_form.gender == '':
            flask.session[constants.ERROR_ATTR] = GENDER_INVALID_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Save the filled parent form to the database and send a link for
        # filling out that form to the specified parent email address.
        db_util.insert_parent_form(new_form)
        parent_account_util.send_cdi_email(new_form)

        last_parms_dict = flask.session['LAST_PARENT_PARAMS']
        last_parms_dict['global_id'] = ''
        last_parms_dict['study_id'] = ''
        last_parms_dict['child_name'] = ''
        last_parms_dict['parent_email'] = ''
        last_parms_dict['birthday'] = ''

        flask.session[constants.CONFIRMATION_ATTR] = PARENT_FORM_SENT_MSG
        return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

    else:
        if 'LAST_PARENT_PARAMS' in flask.session:
            last_entry_info = flask.session.get('LAST_PARENT_PARAMS')
        else:
            last_entry_info = {
                'global_id': '',
                'gender': '',
                'items_excluded': 0,
                'extra_categories': 0,
                'study_id': '',
                'study': '',
                'birthday': '',
                'languages': '',
                'hard_of_hearing': '',
                'child_name': '',
                'parent_email': '',
                'cdi_type': '',
                'total_num_sessions': ''
            }

        return flask.render_template(
            'parent_accounts.html',
            cur_page='edit_parents',
            users=user_util.get_all_users(),
            cdi_formats=db_util.load_cdi_model_listing(),
            gender_male_constant=constants.MALE,
            gender_female_constant=constants.FEMALE,
            gender_other_constant=constants.OTHER_GENDER,
            last_entry_info=last_entry_info,
            **session_util.get_standard_template_values()
        )


@app.route('/base/parent_cdi/_thanks')
def thank_parent_form() -> controller_types.ValidFlaskReturnTypes:
    """Display a landing page thanking a parent for thier input.

    @return: Static HTML page rendering thanking a user for filling out a
        parent CDI form.
    @rtype: str
    """
    return flask.render_template(
        'parent_thanks.html',
        **session_util.get_standard_template_values()
    )


@app.route('/base/parent_cdi/<form_id>', methods=['GET', 'POST'])
def handle_parent_cdi_form(form_id: str) -> controller_types.ValidFlaskReturnTypes:
    """Controller to display and handle a parent CDI form.

    Controller to render a parent CDI form on a GET request and logic to handle
    a completed CDI form on a POST. This will create a new CDI snapshot on
    POST in addition to preventing duplicate submissions of the same form.

    @param form_id: The ID of the parent form to render or to process.
    @type form_id: str
    @return: Static HTML page rendering with a parent CDI form or a redirect
        after a successful submission.
    @rtype: Flask response
    """
    request = flask.request

    # Regardless of GET or POST, ensure that the parent form is valid and refers
    # to a child that can still be found in the database, preventing snapshots
    # that are orphaned.

    # Ensure the parent form still exists (and has not been submitted already).
    parent_form = db_util.get_parent_form_by_id(form_id)
    if not parent_form:
        return flask.render_template(
            'end_parent_form_404.html',
            **session_util.get_standard_template_values()
        ), 404

    # Ensure that the form has global ID information or both a study and study
    # ID.
    form_db_id = parent_form.database_id
    form_study_id = parent_form.study_id
    form_study = parent_form.study
    if form_db_id == None and (form_study_id == None or form_study == None):
        return flask.render_template(
            'end_parent_form_404.html',
            **session_util.get_standard_template_values()
        ), 404

    # Ensure that the selected format is valid and is specified in the databse.
    selected_format_maybe = db_util.load_cdi_model(parent_form.cdi_type)
    if selected_format_maybe == None:
        return flask.render_template(
            'end_parent_form_404.html',
            **session_util.get_standard_template_values()
        ), 404

    selected_format: models.CDIFormat = selected_format_maybe # type: ignore

    if request.method == 'POST':

        # Parse word entries
        count_as_spoken_vals = selected_format.details['count_as_spoken']
        word_entries = {}
        known_words = []
        words_spoken = 0
        successful = True
        total_possible_words = 0
        for category in selected_format.details['categories']:
            for word in category['words']:

                word_val_maybe: typing.Optional[str] = request.form.get(
                    WORD_RESPONSE_ID_TEMPL % word,
                    None
                )

                word_val_int: typing.Optional[int] = None
                if word_val_maybe == None:
                    msg = WORD_VALUE_MISSING_MSG % word
                    flask.session[constants.ERROR_ATTR] = msg
                    successful = False
                else:
                    word_val: str = word_val_maybe # type: ignore
                    word_val_int = interp_util.safe_int_interpret(word_val)

                if word_val_int == None:
                    msg = WORD_VALUE_INVALID_MSG % word
                    flask.session[constants.ERROR_ATTR] = msg
                    successful = False

                word_entries[word.lower().replace('*', '')] = word_val_int

                if word_val_int in count_as_spoken_vals:
                    known_words.append(word)
                    words_spoken += 1
                total_possible_words += 1

        if not successful:
            flask.session['SAVED_WORDS'] = word_entries
            return flask.redirect(request.path)

        # Load the study from the parent form or, if the parent form does not
        # have it, load it form the user's response.
        study = parent_form.study
        if study == None or study == '':
            study = request.form.get('study', None)

        # Load the study ID from the parent form or, if the parent form does not
        # have it, load it form the user's response.
        study_id = parent_form.study_id
        if study_id == None or study_id == '':
            study_id = request.form.get('study_id', None)

        # Load the db ID from the parent form or, if the parent form does not
        # have it, load it form the user's response.
        database_id = parent_form.database_id
        if database_id == None or database_id == '':
            database_id = request.form.get('database_id', None)

        # Ensure that, if only a global ID is provided, that a study and study
        # ID is generated.
        if database_id != None:
            results = parent_account_util.get_snapshot_chronology_for_db_id(
                database_id # type: ignore
            )
        elif study != None and study_id != None:
            results = parent_account_util.get_snapshot_chronology_for_study_id(
                study, # type: ignore
                study_id # type: ignore
            )
        else:
            flask.session[constants.ERROR_ATTR] = NO_ID_MSG
            return flask.redirect(request.path)

        # Ensure that the parent form has birthday information or load it from
        # the user response, checking that it is of appropriate ISO format.
        birthday = parent_form.birthday
        if birthday == None or birthday == '':
            birthday_str: typing.Optional[str] = request.form.get('birthday', None)
            if not parent_account_util.is_birthday_valid(birthday_str):
                msg = BIRTHDAY_INVALID_MSG % birthday_str
                flask.session[constants.ERROR_ATTR] = msg
                flask.session['SAVED_WORDS'] = word_entries
                return flask.redirect(request.path)
            else:
                birthday_parts = birthday_str.split('/') # type: ignore
                # Put year last
                birthday_parts = [
                    birthday_parts[2],
                    birthday_parts[0],
                    birthday_parts[1]
                ]
        else:
            birthday_parts = birthday.split('/') # type: ignore

        # Ensure that the parent form has gender information or load it from
        # the user response, ensuring the gender provided is of an appropriate
        # value.
        gender = parent_form.gender
        if gender == None or gender == '':
            gender = interp_util.safe_int_interpret(
                request.form.get('gender', None)
            )
            if not gender in VALID_GENDER_VALUES:
                flask.session[constants.ERROR_ATTR] = GENDER_INVALID_MSG
                flask.session['SAVED_WORDS'] = word_entries
                return flask.redirect(request.path)

        # Ensure that the parent form has items excluded information or load it
        # from the user response, ensuring the items excluded information
        # provided is a valid value.
        items_excluded = parent_form.items_excluded
        if items_excluded == None or items_excluded == '':
            items_excluded = interp_util.safe_int_interpret(
                request.form.get('items_excluded', None))
            if is_none_or_negative(items_excluded):
                items_excluded = 0

        # Ensure that the parent form has extra categories information or load
        # it from the user response, ensuring the extra categories information
        # provided is a valid value.
        extra_categories = parent_form.extra_categories
        if extra_categories == None or extra_categories == '':
            extra_categories = interp_util.safe_int_interpret(
                request.form.get('extra_categories', None))
            if is_none_or_negative(extra_categories):
                extra_categories = 0

        # Ensure that the parent form has total num sessions info or load
        # it from the user response, ensuring the total number of sessions
        # provided is a valid value.
        total_num_sessions = parent_form.total_num_sessions
        if total_num_sessions == None or total_num_sessions == '':
            total_num_sessions = interp_util.safe_int_interpret(
                request.form.get('total_num_sessions', None))
            if is_none_or_negative(total_num_sessions):
                total_num_sessions = 0

        # Ensure that the parent form has languages information or load it from
        # the user response.
        languages = parent_form.languages
        if languages == None or languages == '':
            languages = request.form.get('languages', None)

        # Ensure that languages information is valid.
        languages_list: typing.List[str] = []
        if languages == None or languages == '':
            flask.session[constants.ERROR_ATTR] = LANGUAGES_NOT_PROVIDED_MSG
            flask.session['SAVED_WORDS'] = word_entries
            return flask.redirect(request.path)
        else:
            languages_list = languages.split(',') # type: ignore

        # Ensure that the parent form has hard of hearing information or load
        # it from the user response, ensuring the hard of hearing information
        # provided is a valid value.
        hard_of_hearing = parent_form.hard_of_hearing
        if hard_of_hearing == None or hard_of_hearing == '':
            provided_val = request.form.get('hard_of_hearing', 'off')
            hard_of_hearing = provided_val == constants.FORM_SELECTED_VALUE

        # Ensure that the parent form has hard of hearing information or load
        # it from the user response, ensuring the hard of hearing information
        # provided is a valid value.
        birthday_date = None
        if len(birthday_parts) != 3:
            age = None
        else:
            try:
                birthday_date = datetime.date(
                    int(birthday_parts[0]),
                    int(birthday_parts[1]),
                    int(birthday_parts[2])
                )
                today = datetime.date.today()
                age = interp_util.monthdelta(birthday_date, today)
                birthday = birthday_date.strftime(DATE_OUT_STR)
            except:
                age = None

        # Determine approach percentiles
        if age:
            percentiles = selected_format.details['percentiles']
            if gender == constants.MALE:
                percentile_table_name = percentiles['male']
            elif gender == constants.FEMALE:
                percentile_table_name = percentiles['female']
            else:
                percentile_table_name = percentiles['other']

            # TODO(samp): This should be in db_util
            # Calculate percentiles
            percentile_model = db_util.load_percentile_model(
                percentile_table_name)
            if percentile_model == None:
                msg = COULD_NOT_FIND_PERCENTILES_MSG
                flask.session[constants.ERROR_ATTR] = msg
                flask.session['SAVED_WORDS'] = word_entries
                return flask.redirect(request.path)

            percentile_model_realized: models.PercentileTable = percentile_model # type: ignore

            percentile = math_util.find_percentile(
                percentile_model_realized.details,
                words_spoken,
                age,
                total_possible_words
            )
        else:
            percentile = -1

        # Find prior entries in study
        if study != None and study_id != None:
            session_number = recalc_util.get_session_number(study, study_id) # type: ignore

        if not total_num_sessions:
            total_num_sessions = session_number

        # Check all required values resolved
        study_id_realized = type_util.assert_not_none(study_id)
        study_realized = type_util.assert_not_none(study)
        gender_realized = type_util.assert_not_none(gender)
        age_realized = type_util.assert_not_none(age)
        birthday_realized = type_util.assert_not_none(birthday)
        items_excluded_realized = type_util.assert_not_none(items_excluded)
        extra_categories_realized = type_util.assert_not_none(extra_categories)
        hard_of_hearing_realized = type_util.assert_not_none(hard_of_hearing)

        # Put in snapshot metadata
        new_snapshot = models.SnapshotMetadata(
            None,
            str(database_id),
            study_id_realized,
            study_realized,
            gender_realized,
            age_realized,
            birthday_realized,
            datetime.date.today().strftime(DATE_OUT_STR),
            session_number,
            total_num_sessions,
            words_spoken,
            items_excluded_realized,
            percentile,
            extra_categories_realized,
            0,
            languages_list,
            len(languages_list),
            selected_format.details['meta']['cdi_type'],
            hard_of_hearing_realized,
            False
        )
        db_util.insert_snapshot(new_snapshot, word_entries)
        db_util.remove_parent_form(form_id)

        flask.session[constants.CONFIRMATION_ATTR] = SUBMITTED_MSG
        flask.session['SAVED_WORDS'] = None
        return flask.redirect(THANK_YOU_MSG_URL)

    else:
        # Get the most recent snapshot
        if parent_form.database_id == None:
            results = []
        else:
            results = parent_account_util.get_snapshot_chronology_for_db_id(
                parent_form.database_id # type: ignore
            )

        saved_known_words = flask.session.get('SAVED_WORDS', None)
        if saved_known_words == {}:
            saved_known_words = None

        def convert_legacy_true(x):
            return constants.EXPLICIT_TRUE if x == constants.LEGACY_TRUE else x

        word_entries = {}
        if saved_known_words:
            word_entries = saved_known_words
        elif len(results) > 0:
            # Find the words known from the last snapshot if that last snapshot
            # is available for reference.
            latest_snapshot = results[0]
            contents = db_util.load_snapshot_contents(latest_snapshot)
            known_words_tuples = map(
                lambda x: (x.word, convert_legacy_true(x.value)),
                contents
            )
            word_entries = dict(known_words_tuples)

        option_values = list(map(
            lambda x: x['value'],
            selected_format.details['options']
        ))

        for option in selected_format.details['options']:
            if 'prefill_value' in option:
                option_values.extend(option['prefill_value'])

        return flask.render_template(
            'end_parent_form.html',
            selected_format=selected_format,
            child_name=parent_form.child_name,
            study=parent_form.study,
            study_id=parent_form.study_id,
            database_id=parent_form.database_id,
            birthday=parent_form.birthday,
            gender=parent_form.gender,
            items_excluded=parent_form.items_excluded,
            total_num_sessions=parent_form.total_num_sessions,
            extra_categories=parent_form.extra_categories,
            languages=parent_form.languages,
            word_entries=word_entries,
            known_vals=[constants.EXPLICIT_TRUE, constants.LEGACY_TRUE],
            male_value=constants.MALE,
            female_value=constants.FEMALE,
            other_gender_value=constants.OTHER_GENDER,
            option_values=option_values,
            num_categories = len(selected_format.details['categories']),
            results=results,
            **session_util.get_standard_template_values()
        )
