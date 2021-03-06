"""Logic for authorizing and responding to API requests.

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
import json
import typing

import flask

from ..struct import models
from ..util import api_key_util
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import report_util
from ..util import interp_util
from ..util import parent_account_util
from ..util import session_util
from ..util import user_util

from . import controller_types

from cdibase import app

SPECIAL_API_QUERY_FIELDS = {
    'min_percentile': {'field': 'percentile', 'op': 'gteq'},
    'max_percentile': {'field': 'percentile', 'op': 'lteq'},
    'min_birthday': {'field': 'birthday', 'op': 'gteq'},
    'max_birthday': {'field': 'birthday', 'op': 'lteq'},
    'min_session_date': {'field': 'session_date', 'op': 'gteq'},
    'max_session_date': {'field': 'session_date', 'op': 'lteq'}
}

FLOAT_FIELDS = [
    'min_percentile',
    'max_percentile'
]

INTEGER_FIELDS = [
    'child_id',
    'gender',
    'session_num',
    'total_num_sessions',
    'words_spoken',
    'items_excluded',
    'extra_categories',
    'revision',
    'num_languages',
    'hard_of_hearing'
]

INGORE_FIELDS = [
    'format',
    'api_key'
]

SUCCESS_JSON_MSG = json.dumps({'msg': 'success'})

DEFAULT_INTERPRETATION_FORMAT = 'standard'

ERROR_ATTR = constants.ERROR_ATTR
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR
FORMAT_ATTR = constants.FORMAT_SESSION_ATTR

API_KEY_FIELD = 'api_key'
NO_API_KEY_MSG = 'No API key provided.'
INVALID_API_KEY_MSG = 'Invalid API key provided.'
USER_NOT_API_AUTHORIZED_MSG = 'User not authorized to use API keys.'
USER_NOT_DB_AUTHORIZED_MSG = 'User not authorized to use access database.'
MISMATCHED_CSV_LENGTHS_MSG = 'Mismatched CSV list lengths.'
MISSING_PARENT_EMAIL_MSG = 'Parent email required.'
NEW_API_KEY_MSG = 'New API key generated.'
MISSING_CDI_TYPE_MSG = 'Must specify cdi_type.'
INVALID_CDI_TYPE_MSG = '%s not a valid cdi_type.'
ISO_DATE_INVALID_MSG = 'Must provide ISO8601 date for birthday.'
INVALID_GENDER_VALUE_MSG = 'The provided gender value is invalid for the ' \
    'selected presentation format.'
INVALID_HARD_OF_HEARING_MSG = 'The provided hard of hearing value is invalid ' \
    'for the selected presentation format.'
NO_ID_MSG = 'Must provide an integer global ID or both a study ID and study ' \
    'name.'
INVALID_PARENT_EMAIL = '%s is unlikely to be a valid email address.'
INVALID_INTERPRETATION_MSG = 'Invalid presentation format name provided.'
ISO_PARSE_STR = '%Y-%m-%d'
DATE_OUT_STR = '%Y/%m/%d'

CHILD_ID_FIELD = 'child_id'
NO_CHILD_ID_MSG = 'No child ID provided.'

INVALID_REQUEST_STATUS = 400
UNAUTHORIZED_STATUS = 403

SNAPSHOTS_DB_TABLE = constants.SNAPSHOTS_DB_TABLE


def generate_error(msg: str, code: int) -> typing.Tuple[str, int]:
    """Generate a JSON serialized error message that the API can return.

    @param msg: The error message to provide to the API client.
    @type msg: str
    @param code: The HTTP status code to report with this error message.
    @type code: int
    @return: A tuple containing the string serialized JSON object with the error
        message as well as the HTTP status code. This can be returned to Flask
        from a Flask request handler.
    @rtype: tuple
    """
    return json.dumps({ERROR_ATTR: msg}), code


def generate_unauthorized_error(msg: str) -> typing.Tuple[str, int]:
    """Generate an error indicating that the user attempted unauthorized action.

    Generate a JSON serialized error message that the API can return indicating
    that there was an unauthorized attempt to execute a sensitive or possibly
    destructive opreation.

    @param msg: The error message to provide to the API client.
    @type msg: str
    @return: A tuple containing the string serialized JSON object with the error
        message as well as the HTTP status code. This can be returned to Flask
        from a Flask request handler.
    @rtype: tuple
    """
    return generate_error(msg, UNAUTHORIZED_STATUS)


def generate_invalid_request_error(msg: str) -> typing.Tuple[str, int]:
    """Return an error showing a user attempted an invalid / incomplete action.

    Generate a JSON serialized error message that the API can return. This error
    will indicate that the user attempted an action with an invalid or
    incomplete request.

    @param msg: The error message to provide to the API client.
    @type msg: str
    @return: A tuple containing the string serialized JSON object with the error
        message as well as the HTTP status code. This can be returned to Flask
        from a Flask request handler.
    @rtype: tuple
    """
    return generate_error(msg, INVALID_REQUEST_STATUS)


def make_filter(field: str, value: str) -> models.Filter:
    """Add a filter to the serialized specification of a database query.

    Creates a Filter object that can be used with a filter_util search query.
    Looks up the provided field in SPECIAL_API_QUERY_FIELDS to determine the
    correct equality operator, defaulting to checking for equality. This also
    inspects FLOAT_FIELDS and INTEGER_FIELDS to find the appropriate type
    conversion. If the field is not specified in those two collections, the
    value is left as a string. Note that this does not respect INGORE_FIELDS and
    this should not be run on fields in that collection.

    @param field: The field to filter on.
    @type field: str
    @param value: The value to look for or to compare against. Will be cast
        based on the field being filtered on so string values are accepted even
        if they actually represent numerical values.
    @type value: str, int, or other primitive
    @return: Filter created
    """
    if field in FLOAT_FIELDS:
        value = float(value) # type: ignore
    elif field in INTEGER_FIELDS:
        value = int(value) # type: ignore

    filter_const_info = None
    if field in SPECIAL_API_QUERY_FIELDS:
        filter_const_info = SPECIAL_API_QUERY_FIELDS[field]
    else:
        filter_const_info = {'field': field, 'op': 'eq'}

    return models.Filter(
        filter_const_info['field'],
        filter_const_info['op'],
        value
    )


def get_api_key_or_none(user_id: typing.Optional[int]) -> typing.Optional[models.APIKey]:
    """Get API key info if not None.

    @param user_id: The user to lookup.
    @returns: Key info if found and user_id is not None.
    """
    if user_id == None:
        return None
    else:
        return api_key_util.get_api_key(user_id) # type: ignore


@app.route('/base/config_api_key')
@session_util.require_login(use_api_key=True)
def config_api_keys() -> controller_types.ValidFlaskReturnTypes:
    """GUI page for configuring API keys.

    @return: Current API key and controls to modify that key.
    @rtype: flask.Response
    """
    user_id = session_util.get_user_id_force()
    return flask.render_template(
        'edit_api_keys.html',
        cur_page='conifg_api_key',
        api_key=get_api_key_or_none(user_id),
        **session_util.get_standard_template_values()
    )


@app.route('/base/config_api_key/new')
@session_util.require_login(use_api_key=True)
def create_api_key() -> controller_types.ValidFlaskReturnTypes:
    """Controller that allows for the creation of a new API key.

    Controller that assigns a user a new API key. Note that this controller will
    invalidate old API keys held by this user as well. This operates on the user
    who owns the current session (the user currently logged in). This controller
    will set the confirmation or error message attribute for the session.

    @return: Redirect to the API configuration page.
    @rtype: Flask response
    """
    user_id = session_util.get_user_id_force()
    api_key_util.create_new_api_key(user_id)
    flask.session[CONFIRMATION_ATTR] = NEW_API_KEY_MSG
    return flask.redirect('/base/config_api_key')


def verify_api_key_for_parent_forms(api_key: typing.Optional[str]) -> typing.Optional[controller_types.ValidFlaskReturnTypes]:
    """Verify that the user with the given API key can send parent CDI forms.

    Check that the given API is valid, active (belongs to a user), that user
    is still authorized to use the API, and that the user has the ability to
    edit / interact with parent data.

    @param api_key: The API key to test.
    @type api_key: str
    @return: Tuple with a string containing a json encoded error object that
        can be returned from the API if there was an error. Returns None if
        there was no error.
    @rtype: tuple or None
    """
    if not api_key:
        return generate_invalid_request_error(NO_API_KEY_MSG)

    api_key_record = db_util.get_api_key(api_key)
    if not api_key_record:
        return generate_invalid_request_error(INVALID_API_KEY_MSG)

    user = user_util.get_user(api_key_record.user_id)
    if not user:
        return generate_invalid_request_error(INVALID_API_KEY_MSG)

    if not user.can_use_api_key:
        return generate_unauthorized_error(USER_NOT_API_AUTHORIZED_MSG)

    if not user.can_edit_parents:
        return generate_unauthorized_error(USER_NOT_DB_AUTHORIZED_MSG)

    return None


@app.route('/base/api/v0/send_parent_form', methods=['GET', 'POST'])
def send_parent_form() -> controller_types.ValidFlaskReturnTypes:
    """API controller that allows external applications to send an CDI form.

    API controller that allows external applications and services to send a
    single CDI form to many parents. All parameters should be provided as form-
    encoded body parameters except for the API key which should be specified in
    the URL as a query string.

    ENDPOINT: /base/api/v0/send_parent_form

    DESCRIPTION: Send a single CDI form to many parents.

    SUPPORTED METHODS: GET, POST

    RESPONSE: JSON-encoded object with a message field. Objects representing an
        error have that message in an "error" attribute.

    All of the following additional query parameters are required:
     - api_key
       // Executes this request on behalf of the user account with this API key.
     - &child_name={{child name}}
       // note that this is never stored in the application or into the CDI db.
     - &cdi_type={{type of CDI form to send}}
       // "fullenglishcdi" without quotes is suggested if uncertain
     - &parent_email={{parent's email address}}

    One of the following is required:
     - &database_id={{kelp db id}}
       // Providing study (see second option) is suggested even if if a study ID
       // cannot be provided.
     - &study={{study name}}&study_id={{child ID within study}}

    Any of the following can be optionally specified:
     - study
       // String with no quotes.
     - gender
       // If "standard" was selected above, use "Male" or "Female" without
       // quotes.
     - birthday
       // ISO 8601
     - items_excluded
       // Integer. 0 suggested if uncertain.
     - extra_categories
       // Integer. 0 suggested if uncertain.
     - languages
       // period seperated list (not commas because of the second API endpoint)
     - hard_of_hearing
       // If "standard" was selected above, use "1" or "0" for true and false
       // respectively. Do not include quotes.
     - &format={{data presentation format}}
       // This indicates what values should be used for true, false, male,
       // female, etc. "standard" without quotes is suggested if uncertain.
       // Defaults to "standard" if not provided.

    If any of these fields are not provided, missing values will be loaded from
    the most recent CDI available for the child or, if there are no prior CDIs
    available within the DB, the parent will be asked for this information
    within the form GUI.

    @return: JSON encoded repsonse as standardized by the API.
    @rtype: str
    """
    request = flask.request
    api_key = request.args.get(API_KEY_FIELD, None)

    # Ensure that the current user has premissions necessary to send parent CDI
    # through the API layer.
    problem = verify_api_key_for_parent_forms(api_key) # type: ignore
    if problem != None:
        return problem # type: ignore

    # Parse user provided information about the interpretation / presentation
    # format, mapping necessary to interpreting user input for this API
    # operation.
    interpretation_format_name = request.args.get(FORMAT_ATTR,
        DEFAULT_INTERPRETATION_FORMAT)
    interpretation_format_maybe = db_util.load_presentation_model(
        interpretation_format_name)

    # Reject API request if the interpretation format was not provided or if the
    # user requested an interpretation format that was not recognized.
    if interpretation_format_maybe == None:
        return generate_invalid_request_error(INVALID_INTERPRETATION_MSG)

    interpretation_format: models.PresentationFormat = interpretation_format_maybe # type: ignore

    # Parse the rest of user input.
    form_id = parent_account_util.generate_unique_cdi_form_id()
    global_id_maybe = request.args.get('database_id', '')
    study_id_maybe = request.args.get('study_id', '')
    study_maybe = request.args.get('study', '')
    gender_maybe = request.args.get('gender', '')
    birthday_maybe = request.args.get('birthday', '')
    items_excluded_maybe = interp_util.safe_int_interpret(
        request.args.get('items_excluded', ''))
    extra_categories_maybe = interp_util.safe_int_interpret(
        request.args.get('extra_categories', ''))
    total_num_sessions_maybe = interp_util.safe_int_interpret(
        request.args.get('total_num_sessions', ''))
    languages = request.args.get('languages', '')
    languages = languages.split('.')
    hard_of_hearing = request.args.get('hard_of_hearing')
    child_name = request.args.get('child_name', '')
    parent_email = request.args.get('parent_email', '')
    cdi_type_maybe = request.args.get('cdi_type', None)

    # Check that an CDI type was provided
    if cdi_type_maybe == None or cdi_type_maybe == '':
        return generate_invalid_request_error(MISSING_CDI_TYPE_MSG)

    cdi_type: str = cdi_type_maybe # type: ignore

    # Ensure that the name of the desired CDI format is specified / exists in
    # the application database.
    if db_util.load_cdi_model(cdi_type) == None: # type: ignore
        msg = INVALID_CDI_TYPE_MSG % cdi_type
        return generate_invalid_request_error(msg)

    # Ensure that either a global ID or both a study and study ID were provided.
    global_id_missing = global_id_maybe == None or global_id_maybe == ''
    study_id_missing = study_id_maybe == None or study_id_maybe == ''
    study_missing = study_maybe == None or study_maybe == ''
    if global_id_missing and (study_id_missing or study_missing):
        return generate_invalid_request_error(NO_ID_MSG)

    # Ensure that the provided parent email address at least has the form of an
    # email address. Note that, due to the asynchronous nature of email, there
    # is currently no mechanism for reporting undelivered emails in this
    # application.
    if not parent_account_util.is_likely_email_address(parent_email):
        message = INVALID_PARENT_EMAIL % parent_email
        return generate_invalid_request_error(message)

    # Check that, if a birthday was provided, that the birthday has an
    # appropriate ISO date format.
    if birthday_maybe != None and birthday_maybe != '':
        try:
            birthday_date = datetime.datetime.strptime(birthday_maybe, ISO_PARSE_STR)
            birthday_maybe = birthday_date.strftime(DATE_OUT_STR)
        except ValueError as e:
            return generate_invalid_request_error(ISO_DATE_INVALID_MSG)

    # Use the specified interpretation / presentation format to parse the
    # provided gender value.
    interpretation_vals = interpretation_format.details
    gender: typing.Optional[int] = None
    if gender_maybe != None and gender_maybe != '':
        if gender_maybe == interpretation_vals['male']:
            gender = constants.MALE
        elif gender_maybe == interpretation_vals['female']:
            gender = constants.FEMALE
        elif gender_maybe == interpretation_vals['explicit_other']:
            gender = constants.OTHER_GENDER
        else:
            return generate_invalid_request_error(INVALID_GENDER_VALUE_MSG)

    # use the specified interpretation / presentation formation to parse the
    # provided hard of hearing status.
    hard_of_hearing_int: typing.Optional[int] = None
    if hard_of_hearing != None and hard_of_hearing != '':
        if isinstance(hard_of_hearing, bool):
            if hard_of_hearing:
                hard_of_hearing_int = constants.EXPLICIT_TRUE
            else:
                hard_of_hearing_int = constants.EXPLICIT_FALSE
        elif isinstance(hard_of_hearing, int):
            hard_of_hearing_int = hard_of_hearing # type: ignore
        elif hard_of_hearing == interpretation_vals['explicit_true']:
            hard_of_hearing_int = constants.EXPLICIT_TRUE
        elif hard_of_hearing == interpretation_vals['explicit_false']:
            hard_of_hearing_int = constants.EXPLICIT_FALSE
        else:
            return generate_invalid_request_error(INVALID_HARD_OF_HEARING_MSG)

    # Create a new parent form model but wait to save it until resolving missing
    # values by using a previous entry for the specified child.
    new_form = models.ParentForm(
        form_id,
        child_name,
        parent_email,
        cdi_type,
        global_id_maybe,
        study_id_maybe,
        study_maybe,
        gender,
        birthday_maybe,
        items_excluded_maybe,
        extra_categories_maybe,
        ','.join(languages),
        len(languages),
        hard_of_hearing_int,
        total_num_sessions_maybe
    )

    # If a parent form model is missing information about a child, load the rest
    # of the missing information from a previous CDI snapshot for the child.
    resolver = parent_account_util.AttributeResolutionResolver()
    resolver.fill_parent_form_defaults(new_form)

    # Save the filled parent form to the database and send a link for filling
    # out that form to the specified parent email address.
    db_util.insert_parent_form(new_form)
    parent_account_util.send_cdi_email(new_form)

    return SUCCESS_JSON_MSG


@app.route('/base/api/v0/send_parent_forms', methods=['GET', 'POST'])
def send_parent_forms() -> controller_types.ValidFlaskReturnTypes:
    """API controller that allows external applications to send many CDI forms.

    API controller that allows external applications and services to send many
    CDI forms to many parents. All parameters should be provided as form-
    encoded body parameters except for the API key which should be specified in
    the URL as a query string.

    All of the following additional query parameters are required:
     - api_key
       // Executes this request on behalf of the user account with this API key.
     - &child_name={{child name}}
       // note that this is never stored in the application or into the CDI db.
     - &cdi_type={{type of CDI form to send}}
       // "fullenglishcdi" without quotes is suggested if uncertain
     - &parent_email={{parent's email address}}

    One of the following is required:
     - &database_id={{kelp db id}}
       // Providing study (see second option) is suggested even if if a study ID
       // cannot be provided.
     - &study={{study name}} &study_id={{child ID within study}}

    Any of the following can be optionally specified:
     - study
       // String with no quotes.
     - gender
       // If "standard" was selected above, use "Male" or "Female" without
       // quotes.
     - birthday
       // ISO 8601
     - items_excluded
       // Integer. 0 suggested if uncertain.
     - extra_categories
       // Integer. 0 suggested if uncertain.
     - languages
       // period seperated list (not commas because of the second API endpoint)
     - hard_of_hearing
       // If "standard" was selected above, use "1" or "0" for true and false
       // respectively. Do not include quotes.
     - &format={{data presentation format}}
       // This indicates what values should be used for true, false, male,
       // female, etc. "standard" without quotes is suggested if uncertain.
       // Defaults to "standard" if not provided.

    All fields (except api_key) take a CSV string (no quotes). Elements are
    zipped together so that the first child_name will be paired with the first
    cdi_type, parent_email, etc. while the second child_name will be paired
    with the second cdi_type and so on. This allows API clients to send many
    emails with only one API call.

    If any of these fields are not provided, missing values will be loaded from
    the most recent CDI available for the child or, if there are no prior CDIs
    available within the DB, the parent will be asked for this information
    within the form GUI.

    @return: JSON encoded repsonse as standardized by the API.
    @rtype: str
    """
    request = flask.request
    api_key = request.args.get(API_KEY_FIELD, None)

    # Ensure that the current user has premissions necessary to send parent CDI
    # through the API layer.
    problem = verify_api_key_for_parent_forms(api_key)
    if problem != None:
        return problem # type: ignore

    # Parse user input.
    global_id_str = request.args.get('database_id', '')
    study_id_str = request.args.get('study_id', '')
    study_str = request.args.get('study', '')
    gender_raw = request.args.get('gender', '')
    birthday_str = request.args.get('birthday', '')
    items_excluded_str = request.args.get('items_excluded', '')
    total_num_sessions_str = request.args.get('total_num_sessions', '')
    extra_categories_str = request.args.get('extra_categories', '')
    languages_str = request.args.get('languages', '')
    hard_of_hearing_raw = request.args.get('hard_of_hearing', '')
    child_name_str = request.args.get('child_name', '')
    parent_email = request.args.get('parent_email', '')
    cdi_type_str = request.args.get('cdi_type', '')

    # Parse user provided information about the interpretation / presentation
    # format, mapping necessary to interpreting user input for this API
    # operation.
    interpretation_format_name = request.args.get(FORMAT_ATTR,
        DEFAULT_INTERPRETATION_FORMAT)
    interpretation_format_maybe = db_util.load_presentation_model(
        interpretation_format_name)

    # Reject API request if the interpretation format was not provided or if the
    # user requested an interpretation format that was not recognized.
    if interpretation_format_maybe == None:
        return generate_invalid_request_error(INVALID_INTERPRETATION_MSG)

    interpretation_format: models.PresentationFormat = interpretation_format_maybe # type: ignore

    # To support sending multiple CDI forms in a single API call, split
    # specified values by comma. Note that this API version does not allow for
    # commas in the strings provided to this call unless they demark one input
    # value from another.
    global_id_vals = api_key_util.interp_csv_field(global_id_str)
    study_id_vals = api_key_util.interp_csv_field(study_id_str)
    study_vals = api_key_util.interp_csv_field(study_str)
    gender_vals = api_key_util.interp_csv_field(gender_raw)
    birthday_vals = api_key_util.interp_csv_field(birthday_str)
    items_excluded_vals = api_key_util.interp_csv_field(items_excluded_str)
    total_num_sessions_vals = api_key_util.interp_csv_field(total_num_sessions_str)
    extra_categories_vals = api_key_util.interp_csv_field(extra_categories_str)
    languages_vals = api_key_util.interp_csv_field(languages_str)
    hard_of_hearing_vals = api_key_util.interp_csv_field(hard_of_hearing_raw)
    child_name_vals = api_key_util.interp_csv_field(child_name_str)
    parent_email_vals = api_key_util.interp_csv_field(parent_email)
    cdi_type_vals = api_key_util.interp_csv_field(cdi_type_str)

    # Ensure that the same number of values were provided for each API
    # parameter for this call.
    lengths = [
        len(global_id_vals),
        len(study_id_vals),
        len(study_vals),
        len(gender_vals),
        len(birthday_vals),
        len(items_excluded_vals),
        len(extra_categories_vals),
        len(languages_vals),
        len(hard_of_hearing_vals),
        len(child_name_vals),
        len(parent_email_vals),
        len(cdi_type_vals),
        len(total_num_sessions_vals)
    ]

    length_set = set(lengths)
    length_set.remove(0)

    if len(length_set) > 1:
        return generate_invalid_request_error(MISMATCHED_CSV_LENGTHS_MSG)
    num_records = list(length_set)[0]

    new_forms = []

    # Pair each element across all parameters, grouping the first indexed value
    # of each parameter array (values loaded from CSV strings), the second
    # indexed value of each parameter array, and so on. Each grouping of
    # parameters results in a parent form sent by email.
    for i in range(0, num_records):

        # Get the grouping of parameters across the parameter arrays. Note that
        # get if avail returns '' if the parameter is not provided.
        global_id = api_key_util.get_if_avail(global_id_vals, i)
        study_id = api_key_util.get_if_avail(study_id_vals, i)
        study = api_key_util.get_if_avail(study_vals, i)
        gender_raw = api_key_util.get_if_avail(gender_vals, i)
        birthday = api_key_util.get_if_avail(birthday_vals, i)
        items_excluded = interp_util.safe_int_interpret(
            api_key_util.get_if_avail(items_excluded_vals, i))
        total_num_sessions = interp_util.safe_int_interpret(
            api_key_util.get_if_avail(total_num_sessions_vals, i))
        extra_categories = interp_util.safe_int_interpret(
            api_key_util.get_if_avail(extra_categories_vals, i))
        languages = api_key_util.get_if_avail(languages_vals, i)
        hard_of_hearing_raw = api_key_util.get_if_avail(hard_of_hearing_vals, i)
        child_name = api_key_util.get_if_avail(child_name_vals, i)
        parent_email = api_key_util.get_if_avail(parent_email_vals, i)
        cdi_type = api_key_util.get_if_avail(cdi_type_vals, i)

        # Generate a new unique randomly generated ID for this new parent form.
        form_id = parent_account_util.generate_unique_cdi_form_id()

        # Ensure the desired type of CDI form  was specified.
        if cdi_type == None or cdi_type == '':
            return generate_invalid_request_error(MISSING_CDI_TYPE_MSG)

        # Ensure that the name of the desired CDI format has been specified /
        # the CDI format is in the application's database.
        if db_util.load_cdi_model(cdi_type) == None:
            msg = INVALID_CDI_TYPE_MSG % cdi_type
            return generate_invalid_request_error(msg)

        # Ensure that the API client provided either a global ID or both a study
        # and study ID.
        global_id_missing = global_id == None or global_id == ''
        study_id_missing = study_id == None or study_id == ''
        study_missing = study == None or study == ''
        if global_id_missing and (study_id_missing or study_missing):
            return generate_invalid_request_error(NO_ID_MSG)

        # Ensure that the provided email address at least has the form of an
        # email address. Note that, due to the asynchronous nature of email,
        # there is currently no mechanism for reporting undelivered emails in
        # this application.
        if not parent_account_util.is_likely_email_address(parent_email):
            message = INVALID_PARENT_EMAIL % parent_email
            return generate_invalid_request_error(message)

        # Ensure that the provided birthday is in a correct ISO date string.
        if birthday != None and birthday != '':
            try:
                birthday_date = datetime.datetime.strptime(birthday, ISO_PARSE_STR)
                birthday = birthday_date.strftime(DATE_OUT_STR)
            except:
                return generate_invalid_request_error(ISO_DATE_INVALID_MSG)

        # Parse the languages as a period seperated value.
        languages_list = languages.split('.')

        interpretation_vals = interpretation_format.details

        # Use the specified interpretation / presentation format to parse the
        # provided gender value.
        gender: typing.Optional[int]
        if gender_raw == None or gender_raw == '':
            gender = None
        else:
            if isinstance(gender_raw, int):
                gender = gender_raw
            elif gender_raw == interpretation_vals['male']:
                gender = constants.MALE
            elif gender_raw == interpretation_vals['female']:
                gender = constants.FEMALE
            elif gender_raw == interpretation_vals['explicit_other']:
                gender = constants.OTHER_GENDER
            else:
                return generate_invalid_request_error(INVALID_GENDER_VALUE_MSG)

        # Use the specified interpretation / presentation formation to parse the
        # provided hard of hearing status.
        hard_of_hearing: typing.Optional[int]
        if hard_of_hearing_raw == None or hard_of_hearing_raw == '':
            hard_of_hearing = None
        else:
            if isinstance(hard_of_hearing_raw, bool):
                if hard_of_hearing_raw:
                    hard_of_hearing = constants.EXPLICIT_TRUE
                else:
                    hard_of_hearing = constants.EXPLICIT_FALSE
            elif isinstance(hard_of_hearing_raw, int):
                hard_of_hearing = hard_of_hearing_raw # type: ignore
            if hard_of_hearing_raw == interpretation_vals['explicit_true']:
                hard_of_hearing = constants.EXPLICIT_TRUE
            elif hard_of_hearing_raw == interpretation_vals['explicit_false']:
                hard_of_hearing = constants.EXPLICIT_FALSE
            else:
                return generate_invalid_request_error(
                    INVALID_HARD_OF_HEARING_MSG
                )

        # Create a new parent form model but wait to save it until resolving
        # missing values by using a previous entry for the specified child.
        new_form = models.ParentForm(
            form_id,
            child_name,
            parent_email,
            cdi_type,
            global_id,
            study_id,
            study,
            gender,
            birthday,
            items_excluded,
            extra_categories,
            ','.join(languages_list),
            len(languages_list),
            hard_of_hearing,
            total_num_sessions
        )

        # If a parent form model is missing information about a child, load the
        # rest of the missing information from a previous CDI snapshot for the
        # child.
        resolver = parent_account_util.AttributeResolutionResolver()
        resolver.fill_parent_form_defaults(new_form)

        new_forms.append(new_form)

    for new_form in new_forms:

        # Save the filled parent form to the database and send a link for
        # filling out that form to the specified parent email address.
        db_util.insert_parent_form(new_form)
        parent_account_util.send_cdi_email(new_form)

    return SUCCESS_JSON_MSG


@app.route("/base/api/v0/cdi_metadata.json")
def get_child_info_by_api() -> controller_types.ValidFlaskReturnTypes:
    """Get information about a child in the CDI database.

    Controller that allows other applications and services to look up CDI
    metadata and information about available results for a chid.

    DESCRIPTION: Get information about children and the CDIs they have
                 completed. Note that this call provides summaries of CDIs and
                 does not return the complete CDIs with their full word
                 listings.

    SUPPORTED METHODS: GET

    REQUIRED PARAMETERS:
     - api_key
       // Executes this request on behalf of the user account with this API key.

    OPTIONAL PARAMETERS:
     - format
       // The format to return responses in. Recommended: "standard" (without
       // quotes).
     - child_id
       // Kelp Child ID.
     - min_percentile
       // Only children at or above this percentile will be returned. (Must be
       // >=0.0 and <=100.0)
     - max_percentile
       // Only children at or below this percentile will be returned. (Must be
       // >=0.0 and <=100.0)
     - min_birthday
       // ISO 8601 date. Only children born after this date will be returned.
       // (ex: 2010/12/30)
     - max_birthday
       // ISO 8601 date. Only children born before this date will be returned.
       // (ex: 2010/12/30)
     - min_session_date
       // ISO 8601 date. Only CDIs taken after this date will be returned.
       // (ex: 2010/12/30)
     - max_session_date
       // ISO 8601 date. Only CDIs taken before this date will be returned.
       // (ex: 2010/12/30)
     - gender
       // Only return children of this gender. (Should be "male" or "female" or
       // "other" without quotes).
     - session_num
       // Children may have many sessions and CDIs. Only return CDIs from the
       // nth session where n = the provided session_num.
     - total_num_sessions
       // Children may have many sessions. Only provide CDIs for those that had
       // exactly this many sessions.
     - words_spoken
       // The raw number of words reported as spoken on the child's CDI.
     - items_excluded
       // Only return CDIs that had this many items excluded while taking the
       // CDI.
     - extra_categories
       // Only return CDIs with this many additional categories included.
     - num_languages
       // Only return children that speak this many languages.
     - hard_of_hearing
       // Only return children that are or are not hard of hearing. (Should be
       // "1" or "0" without quotes).
     - study_id
       // Only return CDIs from the study with this ID.
     - study
       // Only return CDIs from the study by this name.
     - age
       // Only return CDIs taken from children of this age in months.
     - cdi_type
       // Only return CDIs of this type.

    All parameters should be provided as a URI query component.
    """
    api_key = flask.request.args.get(API_KEY_FIELD, None)
    if not api_key:
        return generate_invalid_request_error(NO_API_KEY_MSG)

    api_key_record = db_util.get_api_key(api_key)
    if not api_key_record:
        return generate_invalid_request_error(INVALID_API_KEY_MSG)

    user = user_util.get_user(api_key_record.user_id)
    if not user:
        return generate_invalid_request_error(INVALID_API_KEY_MSG)

    if not user.can_use_api_key:
        return generate_unauthorized_error(USER_NOT_API_AUTHORIZED_MSG)

    if not user.can_access_data:
        return generate_unauthorized_error(USER_NOT_DB_AUTHORIZED_MSG)

    fields = filter(
        lambda x: x[0] not in INGORE_FIELDS,
        flask.request.args.items()
    )
    db_filters = map(lambda x: make_filter(*x), fields)

    present_format = flask.request.args.get(FORMAT_ATTR, None)
    if present_format:
        present_format = db_util.load_presentation_model(present_format)

    matching_snapshots = filter_util.run_search_query(
        db_filters,
        SNAPSHOTS_DB_TABLE,
        True
    )
    serialized_snapshots_by_child_id: typing.Dict[int, typing.List[typing.Dict]] = {}

    for snapshot in matching_snapshots:
        child_id_maybe = snapshot.child_id
        assert child_id_maybe != None

        child_id: int = child_id_maybe # type: ignore

        if not child_id in serialized_snapshots_by_child_id:
            serialized_snapshots_by_child_id[child_id] = []

        snapshot_serialized = report_util.serialize_snapshot(
            snapshot,
            presentation_format=present_format,
            report_dict=True,
            include_words=False
        )

        serialized_snapshots_by_child_id[child_id].append(snapshot_serialized) # type: ignore

    return json.dumps(serialized_snapshots_by_child_id)


@app.route('/base/api/v0/get_child_words.json', methods=['GET', 'POST'])
def get_child_words_by_api() -> controller_types.ValidFlaskReturnTypes:
    """Get the words a child knows and when those words were first learned.

    Controller that allows other applications and services to look up the words
    known by a child.

    DESCRIPTION: Get a listing of the words ever known by a child and when that
                 word was first reported.

    SUPPORTED METHODS: GET

    REQUIRED PARAMETERS:
     - api_key
       // Executes this request on behalf of the user account with this API key.
     - child_id
       // Kelp Child ID.

    All parameters should be provided as a URI query component.
    """
    # Pull parameters
    api_key = flask.request.args.get(API_KEY_FIELD, None)
    if not api_key:
        return generate_invalid_request_error(NO_API_KEY_MSG)

    child_id = flask.request.args.get(CHILD_ID_FIELD, None)
    if not child_id:
        return generate_invalid_request_error(NO_CHILD_ID_MSG)

    api_key_record = db_util.get_api_key(api_key)
    if not api_key_record:
        return generate_invalid_request_error(INVALID_API_KEY_MSG)

    # Check attached account
    user = user_util.get_user(api_key_record.user_id)
    if not user:
        return generate_invalid_request_error(INVALID_API_KEY_MSG)

    if not user.can_use_api_key:
        return generate_unauthorized_error(USER_NOT_API_AUTHORIZED_MSG)

    if not user.can_access_data:
        return generate_unauthorized_error(USER_NOT_DB_AUTHORIZED_MSG)

    # Pull data
    db_filters = [ models.Filter('child_id', 'eq', child_id) ]

    matching_snapshot_metadata = filter_util.run_search_query(
        db_filters,
        SNAPSHOTS_DB_TABLE,
        True
    )

    # Serialize data
    ret_serialization = report_util.summarize_snapshots(
        matching_snapshot_metadata
    )
    return json.dumps({'words': ret_serialization})
