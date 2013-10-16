"""Logic for managing parent accounts and parent MCDI forms.

Loginc for managing parent accounts, sending parent MCDI forms, and processing
MCDI parent form responses.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import datetime

import dateutil.parser as dateutil_parser
import flask

from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import math_util
from ..util import parent_account_util
from ..util import session_util
from ..util import user_util

from ..struct import models

from daxlabbase import app

VALID_GENDER_VALUES = [constants.MALE, constants.FEMALE, constants.OTHER_GENDER]

MCDI_TYPE_NOT_GIVEN_MSG = 'MCDI type required.'
PARENT_EMAIL_NOT_GIVEN_MSG = 'Provided parent email appears not to be a ' \
    'valid email address.'
PARENT_FORM_SENT_MSG = 'MCDI form sent.'
NO_ID_MSG = 'Must provide an integer global ID or both a study ID and study ' \
    'name.'
GLOBAL_ID_MUST_BE_INT_MSG = 'The global database ID for a child must be an ' \
    'integer.'
GENDER_INVALID_MSG = 'The provided gender for this child was not recognized.'
DATE_OUT_STR = '%Y/%m/%d'
DATE_INVALID_MSG = '%s is not a valid date.'
INVALID_ITEMS_EXCLUDED_MSG = 'Invalid items count invalid.'
INVALID_EXTRA_CATEGORIES_MSG = 'Extra categories invalid.'
LANGUAGES_NOT_PROVIDED_MSG = 'Languages list not provided.'
COULD_NOT_FIND_PERCENTILES_MSG = 'Could not find percentile information.'
PARENT_ACCOUNT_CONTROLS_URL = '/base/parent_accounts'


@app.route('/base/parent_accounts', methods=['GET', 'POST'])
@session_util.require_login(edit_parents=True)
def send_mcdi_form():
    """Create and send a parent MCDI form.

    Controller that, on GET, displays controls to send MCDI parent forms by
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
        form_id = parent_account_util.generate_unique_mcdi_form_id()
        global_id = request.form.get('global_id')
        gender = request.form.get('gender')
        items_excluded = request.form.get('items_excluded')
        extra_categories = request.form.get('extra_categories')
        study_id = request.form.get('study_id')
        study = request.form.get('study')
        birthday = request.form.get('birthday')
        languages = request.form.get('languages')
        hard_of_hearing = request.form.get('hard_of_hearing')
        hard_of_hearing = hard_of_hearing == constants.FORM_SELECTED_VALUE
        child_name = request.form.get('child_name')
        parent_email = request.form.get('parent_email')
        mcdi_type = request.form.get('mcdi_type')

        # Check that the MCDI type provided has been defined and can be found
        # in the application database.
        mcdi_model = db_util.load_mcdi_model(mcdi_type)
        if mcdi_type == None or mcdi_type == '' or mcdi_model == None:
            flask.session[constants.ERROR_ATTR] = MCDI_TYPE_NOT_GIVEN_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Ensure either a global child ID was provided or that both a global
        # and study ID are available.
        missing_global_id = global_id == None or global_id == ''
        missing_study_id = study_id == None or study_id == ''
        missing_study = study == None or study == ''
        if missing_global_id and (missing_study_id or missing_study):
            flask.session[constants.ERROR_ATTR] = NO_ID_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # If a global ID was provided, coerce it to an integer or report an
        # invalid global ID.
        if not missing_global_id:
            try:
                global_id = int(global_id)
            except ValueError:
                flask.session[constants.ERROR_ATTR] = GLOBAL_ID_MUST_BE_INT_MSG
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
            birthday = dateutil_parser.parse(birthday)
            birthday = birthday.strftime(DATE_OUT_STR)

        # Use the specified interpretation / presentation formation to parse the
        # provided hard of hearing status.
        if hard_of_hearing != None and hard_of_hearing != '':
            if hard_of_hearing:
                hard_of_hearing = constants.EXPLICIT_TRUE
            else:
                hard_of_hearing = constants.EXPLICIT_FALSE

        # Parse out parent form attributes that are integers.
        global_id = interp_util.safe_int_interpret(global_id)
        gender = interp_util.safe_int_interpret(gender)
        items_excluded = interp_util.safe_int_interpret(items_excluded)
        extra_categories = interp_util.safe_int_interpret(extra_categories)

        # Ensure languages are provided and, if not, reject the request
        if languages != None and languages != '':
            languages = languages.split(',')
            languages_str = ','.join(languages)
            num_languages = len(languages)
        else:
            languages_str = None
            num_languages = None

        # Ensure gender information specified and, if it is, make sure the
        # provided gender value is valid.
        has_gender_info = gender != '' and gender != None
        if has_gender_info and not gender in VALID_GENDER_VALUES:
            flask.session[constants.ERROR_ATTR] = GENDER_INVALID_MSG
            return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

        # Create a new parent form model but wait to save it until resolving 
        # missing values by using a previous entry for the specified child.
        new_form = models.ParentForm(
            form_id,
            child_name,
            parent_email,
            mcdi_type,
            global_id,
            study_id,
            study,
            gender,
            birthday,
            items_excluded,
            extra_categories,
            languages_str,
            num_languages,
            hard_of_hearing
        )

        # If a parent form model is missing information about a child, load the
        # rest of the missing information from a previous MCDI snapshot for the
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
        parent_account_util.send_mcdi_email(new_form)

        flask.session[constants.CONFIRMATION_ATTR] = PARENT_FORM_SENT_MSG
        return flask.redirect(PARENT_ACCOUNT_CONTROLS_URL)

    else:
        return flask.render_template(
            'parent_accounts.html',
            cur_page='edit_parents',
            users=user_util.get_all_users(),
            mcdi_formats=db_util.load_mcdi_model_listing(),
            gender_male_constant=constants.MALE,
            gender_female_constant=constants.FEMALE,
            gender_other_constant=constants.OTHER_GENDER,
            **session_util.get_standard_template_values()
        )


@app.route("/base/parent_mcdi/_thanks")
def thank_parent_form():
    """Display a landing page thanking a parent for thier input.

    @return: Static HTML page rendering thanking a user for filling out a
        parent MCDI form.
    @rtype: str
    """
    return flask.render_template(
        'parent_thanks.html',
        **session_util.get_standard_template_values()
    )


@app.route("/base/parent_mcdi/<form_id>", methods=["GET", "POST"])
def handle_parent_mcdi_form(form_id):
    """Controller to display and handle a parent MCDI form.

    Controller to render a parent MCDI form on a GET request and logic to handle
    a completed MCDI form on a POST. This will create a new MCDI snapshot on
    POST in addition to preventing duplicate submissions of the same form.

    @param form_id: The ID of the parent form to render or to process.
    @type form_id: str
    @return: Static HTML page rendering with a parent MCDI form or a redirect
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
    selected_format = db_util.load_mcdi_model(parent_form.mcdi_type)
    if selected_format == None:
        return flask.render_template(
            'end_parent_form_404.html',
            **session_util.get_standard_template_values()
        ), 404

    if request.method == 'POST':
        
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
            database_id = interp_util.safe_int_interpret(
                request.form.get('database_id', None))

        # Ensure that, if only a global ID is provided, that a study and study
        # ID is generated.
        if database_id != None:
            results = parent_account_util.get_snapshot_chronology_for_db_id(
                database_id)
            if len(results) == 0:
                study = 'not specified'
                study_id = database_id
        else:
            results = parent_account_util.get_snapshot_chronology_for_study_id(
                study, study_id)
            if len(results) == 0:
                flask.session[constants.ERROR_ATTR] = 'No global ID specified.'
                return flask.redirect(request.path)
        
        # Ensure that the parent form has birthday information or load it from
        # the user response, checking that it is of appropriate ISO format.
        birthday = parent_form.birthday
        if birthday == None or birthday == '':
            birthday = request.form.get('birthday', None)
            if not parent_account_util.is_birthday_valid(birthday):
                msg = 'Birthday invalid: %s' % birthday
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect(request.path)
        
        # Ensure that the parent form has gender information or load it from
        # the user response, ensuring the gender provided is of an appropriate
        # value.
        gender = parent_form.gender
        if gender == None or gender == '':
            gender = request.form.get('gender', None)
            if not gender in VALID_GENDER_VALUES:
                flask.session[constants.ERROR_ATTR] = GENDER_INVALID_MSG
                return flask.redirect(request.path)
        
        # Ensure that the parent form has items excluded information or load it
        # from the user response, ensuring the items excluded information
        # provided is a valid value.
        items_excluded = parent_form.items_excluded
        if items_excluded == None or items_excluded == '':
            items_excluded = interp_util.safe_int_interpret(
                request.form.get('items_excluded', None))
            if items_excluded == None or items_excluded < 0:
                flask.session[constants.ERROR_ATTR] = INVALID_ITEMS_EXCLUDED_MSG
                return flask.redirect(request.path)
        
        # Ensure that the parent form has extra categories information or load
        # it from the user response, ensuring the extra categories information
        # provided is a valid value.
        extra_categories = parent_form.extra_categories
        if extra_categories == None or extra_categories == '':
            extra_categories = interp_util.safe_int_interpret(
                request.form.get('extra_categories', None))
            if extra_categories == None or extra_categories < 0:
                msg = INVALID_EXTRA_CATEGORIES_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect(request.path)
        
        # Ensure that the parent form has languages information or load it from
        # the user response.
        languages = parent_form.languages
        if languages == None or languages == '':
            languages = request.form.get('languages', None)

        # Ensure that languages information is valid.
        if languages == None or languages == '':
            flask.session[constants.ERROR_ATTR] = LANGUAGES_NOT_PROVIDED_MSG
            return flask.redirect(request.path)
        else:
            languages = languages.split(',')
        
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
        birthday_parts = birthday.split('/')
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
            except:
                age = None


        # Parse word entries
        count_as_spoken_vals = selected_format.details["count_as_spoken"]
        word_entries = {}
        words_spoken = 0
        total_possible_words = 0
        for category in selected_format.details["categories"]:
            for word in category["words"]:
                word_val = request.form.get("%s_report" % word, None)
                if word_val == None:
                    flask.session["error"] = "%s value missing" % word
                    return flask.redirect(request.path)
                word_val = interp_util.safe_int_interpret(word_val)
                if word_val == None:
                    flask.session["error"] = "%s value invalid" % word
                    return flask.redirect(request.path)
                word_entries[word] = int(word_val)
                if word_val in count_as_spoken_vals:
                    words_spoken += 1
                total_possible_words += 1

        # Determine approach percentiles
        if age:
            percentiles = selected_format.details["percentiles"]
            if gender == constants.MALE:
                percentile_table_name = percentiles["male"]
            elif gender == constants.FEMALE:
                percentile_table_name = percentiles["female"]
            else:
                percentile_table_name = percentiles["other"]

            # TODO(samp): This should be in db_util
            # Calculate percentiles
            percentile_model = db_util.load_percentile_model(
                percentile_table_name)
            if percentile_model == None:
                flask.session["error"] = COULD_NOT_FIND_PERCENTILES_MSG
                return flask.redirect(request.path)
            
            percentile = math_util.find_percentile(
                percentile_model.details,
                words_spoken,
                age,
                total_possible_words
            )
            percentile = int(round(percentile))
        else:
            percentile = -1

        # Find prior entries in study
        study_filter = models.Filter("study", "eq", study)
        study_id_filter = models.Filter("study_id", "eq", study_id)
        results = filter_util.run_search_query([study_filter, study_id_filter],
            "snapshots")
        session_num = len(results) + 1

        # Put in snapshot metadata
        new_snapshot = models.SnapshotMetadata(
            None,
            database_id,
            study_id,
            study,
            gender,
            age,
            birthday,
            datetime.date.today().strftime('%Y/%m/%d'),
            session_num,
            session_num,
            words_spoken,
            items_excluded,
            percentile,
            extra_categories,
            0,
            languages,
            len(languages),
            selected_format.details["meta"]["mcdi_type"],
            hard_of_hearing
        )
        db_util.insert_snapshot(new_snapshot, word_entries)
        db_util.remove_parent_form(form_id)

        flask.session["confirmation"] = 'Form submitted to the lab.'
        return flask.redirect('/base/parent_mcdi/_thanks')

    else:

        # TODO: dedup with form_ values above

        # Get the most recent snapshot
        results = parent_account_util.get_snapshot_chronology_for_db_id(
            parent_form.database_id)

        # Find the words known from the last snapshot if that last snapshot is
        # available for reference.
        if len(results) == 0:
            known_words = []
        else:
            latest_snapshot = results[0]
            contents = db_util.load_snapshot_contents(latest_snapshot)
            known_words_dec = filter(
                lambda x: x.value in constants.TRUE_VALS,
                contents
            )
            known_words = map(
                lambda x: x.word,
                known_words_dec
            )

        return flask.render_template(
            "end_parent_form.html",
            selected_format=selected_format,
            child_name=parent_form.child_name,
            study=parent_form.study,
            study_id=parent_form.study_id,
            database_id=parent_form.database_id,
            birthday=parent_form.birthday,
            gender=parent_form.gender,
            items_excluded=parent_form.items_excluded,
            extra_categories=parent_form.extra_categories,
            languages=parent_form.languages,
            known_words=known_words,
            known_val=constants.EXPLICIT_TRUE,
            **session_util.get_standard_template_values()
        )
