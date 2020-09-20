"""Logic for rendering views and responding to requests related to data entry.

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
import json
import re
import typing

import flask

from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import math_util
from ..util import recalc_util
from ..util import session_util
from ..util import type_util

from ..struct import models

from . import controller_types

from cdibase import app

PARTICIPANT_NOT_FOUND_MSG = '[ not found ]'
CDI_NOT_FOUND_MSG = 'Could not the specified CDI format.'
GLOBAL_ID_NOT_PROVIDED_MSG = 'Participant global id was not provided. Please specify and try again.'
GLOBAL_ID_NOT_GIVEN_MSG = 'Participant global id not given. Please specify and try again.'
STUDY_ID_NOT_PROVIDED_MSG = 'Study id was not provided. Please specify and try again.'
STUDY_NOT_PROVIDED_MSG = 'Study not provided. Please specify and try again.'
GENDER_NOT_PROVIDED_MSG = 'Gender not provided. Please specify and try again.'
GENDER_VALUE_INVALID_MSG = 'Gender value was invalid. Please specify and try again.'
AGE_NOT_PROVIDED_MSG = 'Age not provided. Please specify and try again.'
PARTICIPANT_AGE_INVALID_MSG = 'Participant age should be a number. Please specify and try again.'
BIRTHDAY_NOT_PROVIDED_MSG = 'Birthday not provided. Please specify and try again.'
SESSION_DATE_NOT_PROVIDED_MSG = 'Session date not provided. Please specify and try again.'
SESSION_NUMBER_NOT_PROVIDED_MSG = 'Session number not provided. Please specify and try again.'
SESSION_NUMBER_INVALID_MSG = 'Session number should be a whole number. Please specify and try again.'
ITEMS_EXCLUDED_NOT_PROVIDED_MSG = 'Items excluded not provided. Please specify and try again.'
ITEMS_EXCLUDED_INVALID_MSG = 'Items excluded should be a whole number. Please specify and try again.'
EXTRA_CATEGORIES_NOT_PROVIDED_MSG = 'Extra categories not provided. Please specify and try again.'
EXTRA_CATEGORIES_INVALID_MSG = 'Extra categories should be a whole number. Please specify and try again.'
TOTAL_NUM_SESSION_NOT_PROVIDED_MSG = 'Total number sessions was empty. Please specify and try again.'
NUM_SESSION_INVALID_MSG = 'Total number sessions should be a whole number. Please specify and try again.'
BIRTHDAY_INVALID_FORMAT_MSG = 'Birthday must be of form YYYY/MM/DD. Please specify and try again.'
BIRTHDAY_INVALID_FORMAT_REARRANGE_MSG = 'Birthday entered in incorrect format. Please specify and try again.'
SESSION_DATE_INVALID_FORMAT_MSG = 'Session date must be of form YYYY/MM/DD. Please specify and try again.'
WORD_VALUE_MISSING_MSG = '%s value missing. Please specify and try again.'
WORD_VALUE_INVALID_MSG = '%s value invalid. Please check and try again.'
CDI_ADDED_MSG = 'CDI record added for participant %s.'
ENTER_DATA_URL = '/base/enter_data'
NEW_CHILD_CDI_ADDED_MSG = 'New child and CDI added.'
DATE_REGEX = re.compile('\d{4}/\d{1,2}/\d{1,2}')


@app.route('/base/enter_data')
@session_util.require_login(enter_data=True)
def enter_data_index() -> controller_types.ValidFlaskReturnTypes:
    """Controller for listing of various forms / CDI types.

    Controller for listing of the forms / CDI types the application has access
    to which can be turned into HTML forms.

    @return: Index page with a listing of existing data entry formats and a link
        to upload new ones.
    @rtype: flask.Response
    """
    return flask.render_template(
        'enter_data.html',
        cur_page='enter_data',
        formats=db_util.load_cdi_model_listing(),
        **session_util.get_standard_template_values()
    )


@app.route('/base/enter_data/<format_name>', methods=['GET', 'POST'])
@session_util.require_login(enter_data=True)
def enter_data_form(format_name: str) -> controller_types.ValidFlaskReturnTypes:
    """Actual data entry form controller.

    GET displays the form for a version of CDI or other structure the lab
    tracks. POST submits form into database.

    @param format_name: The name of the form of the CDI to turn into an HTML
        form to fill out.
    @type format_name: str
    @return: HTML form on GET and redirect on POST or error.
    @rtype: flask.Response
    """
    request = flask.request

    selected_format_maybe = db_util.load_cdi_model(format_name)
    if selected_format_maybe == None:
        flask.session[constants.ERROR_ATTR] = CDI_NOT_FOUND_MSG
        return flask.redirect(ENTER_DATA_URL)

    selected_format: models.CDIFormat = selected_format_maybe # type: ignore

    # Render form
    if request.method == 'GET':
        return flask.render_template(
            'enter_data_form.html',
            cur_page='enter_data',
            selected_format=selected_format,
            formats=db_util.load_cdi_model_listing(),
            male_val=constants.MALE,
            female_val=constants.FEMALE,
            other_gender_val=constants.OTHER_GENDER,
            **session_util.get_standard_template_values()
        )

    # Add new data
    else:

        # Snaptshot metadata form data
        global_id = request.form.get('global_id', '')
        study_id = request.form.get('study_id', '')
        study = request.form.get('study', '')
        gender_str = request.form.get('gender', '')
        age_str = request.form.get('age', '')
        birthday = request.form.get('birthday', '')
        session_date = request.form.get('session_date', '')
        session_num_str = request.form.get('session_num', '')
        items_excluded_str = request.form.get('items_excluded', '')
        extra_categories_str = request.form.get('extra_categories', '')
        total_num_sessions_str = request.form.get('total_num_sessions', '')
        hard_of_hearing = request.form.get('hard_of_hearing', 'off')
        hard_of_hearing = hard_of_hearing == constants.FORM_SELECTED_VALUE

        # Check inclusion and interpret submission
        error = None
        if global_id == None or global_id == '':
            error = GLOBAL_ID_NOT_GIVEN_MSG

        if study_id == '':
            error = STUDY_ID_NOT_PROVIDED_MSG

        if study == '':
            error = STUDY_NOT_PROVIDED_MSG

        gender: typing.Optional[int] = None
        if gender_str == '':
            error = GENDER_NOT_PROVIDED_MSG
        else:
            gender = interp_util.safe_int_interpret(gender_str)
            if gender == None:
                error = GENDER_VALUE_INVALID_MSG

        age: typing.Optional[float] = None
        if age_str == '':
            error = AGE_NOT_PROVIDED_MSG
        else:
            age = interp_util.safe_float_interpret(age_str)
            if age == None:
                error = PARTICIPANT_AGE_INVALID_MSG

        if birthday == '':
            error = BIRTHDAY_NOT_PROVIDED_MSG
        if not DATE_REGEX.match(birthday):
            error = BIRTHDAY_INVALID_FORMAT_MSG

        if session_date == '':
            error = SESSION_DATE_NOT_PROVIDED_MSG
        if not DATE_REGEX.match(session_date):
            error = SESSION_DATE_INVALID_FORMAT_MSG

        session_num: typing.Optional[int] = None
        if session_num_str == '':
            error = SESSION_NUMBER_NOT_PROVIDED_MSG
        else:
            session_num = interp_util.safe_int_interpret(session_num_str)
            if session_num == None:
                error = SESSION_NUMBER_INVALID_MSG

        items_excluded: typing.Optional[int] = None
        if items_excluded_str == '':
            error = ITEMS_EXCLUDED_NOT_PROVIDED_MSG
        else:
            items_excluded = interp_util.safe_int_interpret(items_excluded_str)
            if items_excluded == None:
                error = ITEMS_EXCLUDED_INVALID_MSG

        extra_categories: typing.Optional[int] = None
        if extra_categories_str == '':
            error = EXTRA_CATEGORIES_NOT_PROVIDED_MSG
        else:
            extra_categories = interp_util.safe_int_interpret(extra_categories_str)
            if extra_categories == None:
                error = EXTRA_CATEGORIES_INVALID_MSG

        total_num_sessions: typing.Optional[int] = None
        if total_num_sessions_str == '':
            error = TOTAL_NUM_SESSION_NOT_PROVIDED_MSG
        else:
            total_num_sessions = interp_util.safe_int_interpret(
                total_num_sessions_str
            )
            if total_num_sessions == None:
                error = NUM_SESSION_INVALID_MSG

        if error:
            flask.session[constants.ERROR_ATTR] = error
            return flask.redirect(request.path)

        if hard_of_hearing: hard_of_hearing = constants.EXPLICIT_TRUE
        else: hard_of_hearing = constants.EXPLICIT_FALSE

        revision = 0

        # Realize required values
        age_realized: float = type_util.assert_not_none(age)
        global_id_realized: str = type_util.assert_not_none(global_id)
        gender_realized: int = type_util.assert_not_none(gender)
        session_num_realized: int = type_util.assert_not_none(session_num)
        total_num_sessions_realized: int = type_util.assert_not_none(total_num_sessions)
        items_excluded_realized: int = type_util.assert_not_none(items_excluded)
        extra_categories_realized: int = type_util.assert_not_none(extra_categories)

        # Parse word entries
        languages = set()
        count_as_spoken_vals = selected_format.details['count_as_spoken']
        word_entries: typing.Dict[str, int] = {}
        words_spoken = 0
        total_possible_words = 0
        for category in selected_format.details['categories']:
            languages.add(category['language'])
            for word in category['words']:

                word_val = request.form.get('%s_report' % word, None)

                if word_val == None:
                    msg = WORD_VALUE_MISSING_MSG % word
                    flask.session[constants.ERROR_ATTR] = msg
                    return flask.redirect(request.path)

                word_val = interp_util.safe_int_interpret(word_val)
                if word_val == None:
                    msg = WORD_VALUE_INVALID_MSG % word
                    flask.session[constants.ERROR_ATTR] = msg
                    return flask.redirect(request.path)

                word_val_realized: int = word_val # type: ignore
                word_entries[word] = int(word_val_realized)

                if word_val in count_as_spoken_vals:
                    words_spoken += 1

                total_possible_words += 1

        # Determine approach percentiles
        percentiles = selected_format.details['percentiles']
        if gender == constants.MALE:
            percentile_table_name = percentiles['male']
        elif gender == constants.FEMALE:
            percentile_table_name = percentiles['female']
        else:
            percentile_table_name = percentiles['other']

        # TODO(samp): This should be in db_util
        # Calculate percentiles
        percentile_model = db_util.load_percentile_model(percentile_table_name)
        if percentile_model == None:
            flask.session[constants.ERROR_ATTR] = 'Missing percentile model'
            return flask.redirect(request.path)

        percentile_model_realized: model.PercentileTable = percentile_model # type: ignore
        percentile = math_util.find_percentile(
            percentile_model_realized.details,
            words_spoken,
            age_realized,
            total_possible_words
        )

        # Put in snapshot metadata
        new_snapshot = models.SnapshotMetadata(
            None,
            global_id_realized,
            study_id,
            study,
            gender_realized,
            age_realized,
            birthday,
            session_date,
            session_num_realized,
            total_num_sessions_realized,
            words_spoken,
            items_excluded_realized,
            percentile,
            extra_categories_realized,
            revision,
            list(languages),
            len(languages),
            selected_format.details['meta']['cdi_type'],
            hard_of_hearing,
            False
        )

        db_util.report_usage(
            session_util.get_user_email(),
            "Enter Data",
            json.dumps({
                "global_id": global_id,
                "study_id": study_id,
                "study": study
            })
        )

        db_util.insert_snapshot(new_snapshot, word_entries)

        if global_id != None:
            msg = CDI_ADDED_MSG % global_id
        else:
            msg = NEW_CHILD_CDI_ADDED_MSG
        flask.session[constants.CONFIRMATION_ATTR] = msg

        return flask.redirect(request.path)


@app.route('/base/enter_data/lookup_global_id/<study_name>/<participant_study_id>')
@session_util.require_login(enter_data=True)
def lookup_global_id(study_name: str,
        participant_study_id: str) -> controller_types.ValidFlaskReturnTypes:
    """Load find the global ID for a participant given his / her study info.

    Application accessible HTTP handler to find the the global ID for a
    participant given his / her study name and participant study ID.

    @param study_name: The name of the study to find the target participant
        in.
    @type study_name: str
    @param participant_study_id: The ID of the target research participant
        within the provided study.
    @type participant_study_id: str
    @return: Flask repsonse with the participant global ID as a string body (not
        in JSON document).
    @rtype: flask.Response
    """
    global_id = db_util.lookup_global_participant_id(study_name,
        participant_study_id)
    if global_id == None:
        return flask.Response(PARTICIPANT_NOT_FOUND_MSG)
    else:
        return flask.Response(str(global_id))


@app.route('/base/edit_data/lookup_user', methods=['POST'])
@session_util.require_login(enter_data=True)
def lookup_studies() -> controller_types.ValidFlaskReturnTypes:
    """Lookup the studies, global DB ID, and metadata for a participant.

    Lookup the global DB ID for a participant along with their studies and
    study IDs as well as their current metadata (birthday, hard of hearing,
    etc). This aids in helping users correct or update participant metadata.

    @return: Flask reponse with JSON document containing a global ID (integer)
        and studies (list) that itself contains objects with a study (string)
        and study_id (integer).
    @rtype: flask.Response or compatible
    """
    request = flask.request
    lookup_method = request.form['method']

    # Get the global ID
    if lookup_method == 'by_study_id':
        study_id = request.form['study_id']
        if study_id == None or study_id == '':
            return ('Study ID not provided', 404)
        study = request.form['study']
        global_id = db_util.lookup_global_participant_id(study, study_id)
    elif lookup_method == 'by_global_id':
        global_id = request.form['global_id']
        if global_id == None: return ('Global ID not provided', 404)
    else:
        return ('Invalid lookup method', 400)

    global_id_realized = type_util.assert_not_none(global_id)

    # Look up studies
    filters = [models.Filter('child_id', 'eq', global_id_realized)]
    results = filter_util.run_search_query(
        filters,
        constants.SNAPSHOTS_DB_TABLE
    )

    # Check if results available
    if len(results) == 0:
        return ('No participant found.', 404)

    # Extract metadata from most recent snapshot
    most_recent_cdi = results[-1]
    metadata = {
        'gender': most_recent_cdi.gender,
        'birthday': most_recent_cdi.birthday,
        'hard_of_hearing': most_recent_cdi.hard_of_hearing,
        'languages': most_recent_cdi.languages
    }

    # Find unique set of study and study IDs
    ret_cdi_list = []
    for result in results:
        cdi = {
            'study': result.study,
            'study_id': result.study_id,
            'date': result.session_date,
            'id': result.session_num
        }
        ret_cdi_list.append(cdi)
    ret_cdi_list.sort(key=lambda x: x['date'])

    # Serialize and return to user as JSON
    ret_dict = {
        'global_id': global_id,
        'cdis': ret_cdi_list,
        'metadata': metadata
    }

    return json.dumps(ret_dict)


@app.route('/base/edit_data')
@session_util.require_login(enter_data=True)
def render_edit_metadata_ui() -> controller_types.ValidFlaskReturnTypes:
    """Display UI that allows the user to update participant metadata.

    Display UI that allows the user to update participant demographic and other
    personal information such as birthdate, hard of hearing status, gender,
    etc.

    @return: Rendered edit participant UI
    @rtype: flask.Response or equivalent
    """
    return flask.render_template(
        'edit_data.html',
        cur_page='edit_data',
        male_val=constants.MALE,
        female_val=constants.FEMALE,
        other_gender_val=constants.OTHER_GENDER,
        true_val=constants.EXPLICIT_TRUE,
        false_val=constants.EXPLICIT_FALSE,
        **session_util.get_standard_template_values()
    )

@app.route('/base/edit_data', methods=['POST'])
@session_util.require_login(enter_data=True)
def edit_metadata() -> controller_types.ValidFlaskReturnTypes:
    """Edit the metadata for a participant.

    @return: Response with error or confirming operation.
    @rtype: flask.Response or equivalent
    """
    request = flask.request
    error = None

    # Parse incoming new metadata
    global_id = request.form['global_id']
    gender = interp_util.safe_int_interpret(request.form['gender'])
    birthday_raw = request.form['birthday']
    languages = request.form['languages'].split(',')
    hard_of_hearing = interp_util.safe_int_interpret(
        request.form['hard_of_hearing']
    )

    # Check an interpret new metadata values
    if global_id == None:
        error = GLOBAL_ID_NOT_PROVIDED_MSG

    if gender == None:
        error = GENDER_NOT_PROVIDED_MSG

    if birthday_raw == '':
        error = BIRTHDAY_NOT_PROVIDED_MSG
    if not DATE_REGEX.match(birthday_raw):
        error = BIRTHDAY_INVALID_FORMAT_REARRANGE_MSG

    if error:
        return (error, 400)

    db_util.report_usage(
        session_util.get_user_email(),
        'Update Metadata',
        json.dumps({
            'global_id': global_id
        })
    )

    # Realize required values
    gender_realized = type_util.assert_not_none(gender)
    hard_of_hearing_realized = type_util.assert_not_none(hard_of_hearing)

    # Update the snapshots
    db_util.update_participant_metadata(
        global_id,
        gender_realized,
        birthday_raw,
        hard_of_hearing_realized,
        languages,
        snapshot_ids=json.loads(request.form['snapshot_ids'])
    )

    # Recalculate percentiles
    filters = [models.Filter('child_id', 'eq', global_id)]
    snapshots = filter_util.run_search_query(
        filters,
        constants.SNAPSHOTS_DB_TABLE
    )
    recalc_util.recalculate_ages_and_percentiles(snapshots)

    return json.dumps({'result': 'updated'})
