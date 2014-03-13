"""Logic for rendering views and responding to requests related to data entry.

@author: Sam Pottinger
@license: GNU GPL v3
"""

import re

import flask

from ..util import constants
from ..util import db_util
from ..util import interp_util
from ..util import math_util
from ..struct import models
from ..util import session_util

from daxlabbase import app

PARTICIPANT_NOT_FOUND_MSG = '[ not found ]'
MCDI_NOT_FOUND_MSG = 'Could not the specified MCDI format.'
GLOBAL_ID_NOT_PROVIDED_MSG = 'Participant global id was not provided.'
GLOBAL_ID_NOT_INT_MSG = 'Participant global id should be a whole number.'
STUDY_ID_NOT_PROVIDED_MSG = 'Study id was not provided.'
STUDY_NOT_PROVIDED_MSG = 'Study not provided.'
GENDER_NOT_PROVIDED_MSG = 'Gender not provided.'
GENDER_VALUE_INVALID_MSG = 'Gender value was invalid.'
AGE_NOT_PROVIDED_MSG = 'Age not provided.'
PARTICIPANT_AGE_INVALID_MSG = 'Participant age should be a number.'
BIRTHDAY_NOT_PROVIDED_MSG = 'Birthday not provided.'
SESSION_DATE_NOT_PROVIDED_MSG = 'Session date not provided.'
SESSION_NUMBER_NOT_PROVIDED_MSG = 'Session number not provided.'
SESSION_NUMBER_INVALID_MSG = 'Session number should be a whole number.'
ITEMS_EXCLUDED_NOT_PROVIDED_MSG = 'Items excluded not provided.'
ITEMS_EXCLUDED_INVALID_MSG = 'Items excluded should be a whole number.'
EXTRA_CATEGORIES_NOT_PROVIDED_MSG = 'Extra categories not provided.'
EXTRA_CATEGORIES_INVALID_MSG = 'Extra categories should be a whole number.'
TOTAL_NUM_SESSION_NOT_PROVIDED_MSG = 'Total number sessions was empty.'
NUM_SESSION_INVALID_MSG = 'Total number sessions should be a whole number.'
BIRTHDAY_INVALID_FORMAT_MSG = 'Birthday must be of form YYYY/MM/DD.'
SESSION_DATE_INVALID_FORMAT_MSG = 'Session date must be of form YYYY/MM/DD.'
WORD_VALUE_MISSING_MSG = '%s value missing.'
WORD_VALUE_INVALID_MSG = '%s value invalid'
MCDI_ADDED_MSG = 'MCDI record added for participant %d.'
ENTER_DATA_URL = '/base/enter_data'
NEW_CHILD_MCDI_ADDED_MSG = 'New child and MCDI added.'
DATE_REGEX = re.compile('\d{4}/\d{1,2}/\d{1,2}')


@app.route('/base/enter_data')
@session_util.require_login(enter_data=True)
def enter_data_index():
    """Controller for listing of various forms / MCDI types.

    Controller for listing of the forms / MCDI types the application has access
    to which can be turned into HTML forms.

    @return: Index page with a listing of existing data entry formats and a link
        to upload new ones.
    @rtype: flask.Response
    """
    return flask.render_template(
        'enter_data.html',
        cur_page='enter_data',
        formats=db_util.load_mcdi_model_listing(),
        **session_util.get_standard_template_values()
    )


@app.route('/base/enter_data/<format_name>', methods=['GET', 'POST'])
@session_util.require_login(enter_data=True)
def enter_data_form(format_name):
    """Actual data entry form controller.

    GET displays the form for a version of MCDI or other structure the lab
    tracks. POST submits form into database.

    @param format_name: The name of the form of the MCDI to turn into an HTML
        form to fill out.
    @type format_name: str
    @return: HTML form on GET and redirect on POST or error.
    @rtype: flask.Response
    """
    request = flask.request

    selected_format = db_util.load_mcdi_model(format_name)
    if selected_format == None:
        flask.session[constants.ERROR_ATTR] = MCDI_NOT_FOUND_MSG
        return flask.redirect(ENTER_DATA_URL)

    # Render form
    if request.method == 'GET':
        return flask.render_template(
            'enter_data_form.html',
            cur_page='enter_data',
            selected_format=selected_format,
            formats=db_util.load_mcdi_model_listing(),
            male_val=constants.MALE,
            female_val=constants.FEMALE,
            other_gender_val=constants.OTHER_GENDER,
            **session_util.get_standard_template_values()
        )

    # Add new data
    elif request.method == 'POST':

        # Snaptshot metadata form data
        global_id = request.form.get('global_id', '')
        study_id = request.form.get('study_id', '')
        study = request.form.get('study', '')
        gender = request.form.get('gender', '')
        age = request.form.get('age', '')
        birthday = request.form.get('birthday', '')
        session_date = request.form.get('session_date', '')
        session_num = request.form.get('session_num', '')
        items_excluded = request.form.get('items_excluded', '')
        extra_categories = request.form.get('extra_categories', '')
        total_num_sessions = request.form.get('total_num_sessions', '')
        hard_of_hearing = request.form.get('hard_of_hearing', 'off')
        hard_of_hearing = hard_of_hearing == constants.FORM_SELECTED_VALUE

        # Check inclusion and interpret submission
        error = None
        if global_id != '':
            global_id = interp_util.safe_int_interpret(global_id)
            if global_id == None:
                error = GLOBAL_ID_NOT_INT_MSG
        else:
            global_id = None
        
        if study_id == '':
            error = STUDY_ID_NOT_PROVIDED_MSG

        if study == '':
            error = STUDY_NOT_PROVIDED_MSG

        if gender == '':
            error = GENDER_NOT_PROVIDED_MSG
        else:
            gender = interp_util.safe_int_interpret(gender)
            if gender == None:
                error = GENDER_VALUE_INVALID_MSG

        if age == '':
            error = AGE_NOT_PROVIDED_MSG
        else:
            age = interp_util.safe_float_interpret(age)
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

        if session_num == '':
            error = SESSION_NUMBER_NOT_PROVIDED_MSG
        else:
            session_num = interp_util.safe_int_interpret(session_num)
            if session_num == None:
                error = SESSION_NUMBER_INVALID_MSG

        if items_excluded == '':
            error = ITEMS_EXCLUDED_NOT_PROVIDED_MSG
        else:
            items_excluded = interp_util.safe_int_interpret(items_excluded)
            if items_excluded == None:
                error = ITEMS_EXCLUDED_INVALID_MSG

        if extra_categories == '':
            error = EXTRA_CATEGORIES_NOT_PROVIDED_MSG
        else:
            extra_categories = interp_util.safe_int_interpret(extra_categories)
            if extra_categories == None:
                error = EXTRA_CATEGORIES_INVALID_MSG

        if total_num_sessions == '':
            error = TOTAL_NUM_SESSION_NOT_PROVIDED_MSG
        else:
            total_num_sessions = interp_util.safe_int_interpret(
                total_num_sessions)
            if total_num_sessions == None:
                error = NUM_SESSION_INVALID_MSG

        if error:
            flask.session[constants.ERROR_ATTR] = error
            return flask.redirect(request.path)

        if hard_of_hearing: hard_of_hearing = constants.EXPLICIT_TRUE
        else: hard_of_hearing = constants.EXPLICIT_FALSE

        revision = 0

        # Parse word entries
        languages = set()
        count_as_spoken_vals = selected_format.details['count_as_spoken']
        word_entries = {}
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
                word_entries[word] = int(word_val)
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
        percentile = math_util.find_percentile(
            percentile_model.details,
            words_spoken,
            age,
            total_possible_words
        )

        # Put in snapshot metadata
        new_snapshot = models.SnapshotMetadata(
            None,
            global_id,
            study_id,
            study,
            gender,
            age,
            birthday,
            session_date,
            session_num,
            total_num_sessions,
            words_spoken,
            items_excluded,
            percentile,
            extra_categories,
            revision,
            languages,
            len(languages),
            selected_format.details['meta']['mcdi_type'],
            hard_of_hearing,
            False
        )

        db_util.insert_snapshot(new_snapshot, word_entries)

        if global_id != None:
            msg = MCDI_ADDED_MSG % global_id
        else:
            msg = NEW_CHILD_MCDI_ADDED_MSG
        flask.session[constants.CONFIRMATION_ATTR] = msg

        return flask.redirect(request.path)


@app.route('/base/enter_data/lookup_global_id/<study_name>/<participant_study_id>')
@session_util.require_login(enter_data=True)
def lookup_global_id(study_name, participant_study_id):
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
