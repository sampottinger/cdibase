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


@app.route('/base/parent_accounts', methods=['GET', 'POST'])
@session_util.require_login(edit_parents=True)
def send_mcdi_form():
    """Create and send a parent MCDI form.

    @return: HTML page for creating parent forms if a GET request. Redirect
        if POST. Session confirmation and error messages will be set by this
        handler.
    @rtype: Flask response.
    """
    request = flask.request
    if request.method == 'POST':
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

        mcdi_model = db_util.load_mcdi_model(mcdi_type)
        if mcdi_type == None or mcdi_type == '' or mcdi_model == None:
            flask.session[constants.ERROR_ATTR] = MCDI_TYPE_NOT_GIVEN_MSG
            return flask.redirect('/base/parent_accounts')

        missing_global_id = global_id == None or global_id == ''
        missing_study_id = study_id == None or study_id == ''
        missing_study = study == None or study == ''
        if missing_global_id and (missing_study_id or missing_study):
            flask.session[constants.ERROR_ATTR] = NO_ID_MSG
            return flask.redirect('/base/parent_accounts')

        if not missing_global_id:
            try:
                global_id = int(global_id)
            except ValueError:
                flask.session[constants.ERROR_ATTR] = GLOBAL_ID_MUST_BE_INT_MSG
                return flask.redirect('/base/parent_accounts')

        if not parent_account_util.is_likely_email_address(parent_email):
            flask.session[constants.ERROR_ATTR] = PARENT_EMAIL_NOT_GIVEN_MSG
            return flask.redirect('/base/parent_accounts')

        if birthday != None and birthday != '':
            try:
                birthday = dateutil_parser.parse(birthday)
            except ValueError:
                msg = DATE_INVALID_MSG % birthday
                flask.session[constants.ERROR_ATTR] = msg,
                return flask.redirect('/base/parent_accounts')
            birthday = birthday.strftime(DATE_OUT_STR)

        if hard_of_hearing != None and hard_of_hearing != '':
            if hard_of_hearing:
                hard_of_hearing = constants.EXPLICIT_TRUE
            else:
                hard_of_hearing = constants.EXPLICIT_FALSE

        global_id = interp_util.safe_int_interpret(global_id)
        gender = interp_util.safe_int_interpret(gender)
        items_excluded = interp_util.safe_int_interpret(items_excluded)
        extra_categories = interp_util.safe_int_interpret(extra_categories)

        if languages != None and languages != '':
            languages = languages.split(',')
            languages_str = ','.join(languages)
            num_languages = len(languages)
        else:
            languages_str = None
            num_languages = None

        has_gender_info = gender != '' and gender != None
        if has_gender_info and not gender in VALID_GENDER_VALUES:
            flask.session[constants.ERROR_ATTR] = GENDER_INVALID_MSG
            return flask.redirect('/base/parent_accounts')

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

        resolver = parent_account_util.AttributeResolutionResolver()
        resolver.fill_parent_form_defaults(new_form)

        db_util.insert_parent_form(new_form)
        parent_account_util.send_mcdi_email(new_form)

        flask.session[constants.CONFIRMATION_ATTR] = PARENT_FORM_SENT_MSG

        return flask.redirect('/base/parent_accounts')

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
    return flask.render_template(
        "parent_thanks.html",
        **session_util.get_standard_template_values()
    )


@app.route("/base/parent_mcdi/<form_id>", methods=["GET", "POST"])
def handle_parent_mcdi_form(form_id):
    request = flask.request

    parent_form = db_util.get_parent_form_by_id(form_id)
    if not parent_form:
        return flask.render_template(
            "end_parent_form_404.html",
            **session_util.get_standard_template_values()
        ), 404

    selected_format = db_util.load_mcdi_model(parent_form.mcdi_type)

    if request.method == 'POST':
        
        study = parent_form.study
        if study == None or study == '':
            study = request.form['study']
        
        study_id = parent_form.study_id
        if study_id == None or study_id == '':
            study_id = request.form['study_id']
        
        database_id = parent_form.database_id
        if database_id == None or database_id == '':
            database_id = interp_util.safe_int_interpret(
                request.form['database_id'])
        
        birthday = parent_form.birthday
        if birthday == None or birthday == '':
            birthday = request.form['birthday']
        
        gender = parent_form.gender
        if gender == None or gender == '':
            gender = request.form['gender']
        
        items_excluded = parent_form.items_excluded
        if items_excluded == None or items_excluded == '':
            items_excluded = interp_util.safe_int_interpret(
                request.form['items_excluded'])
        
        extra_categories = parent_form.extra_categories
        if extra_categories == None or extra_categories == '':
            extra_categories = interp_util.safe_int_interpret(
                request.form['extra_categories'])
        
        languages = parent_form.languages
        if languages == None or languages == '':
            languages = request.form['languages']
        languages = languages.split(',')
        
        hard_of_hearing = parent_form.hard_of_hearing
        if hard_of_hearing == None or hard_of_hearing == '':
            hard_of_hearing = request.form.get('hard_of_hearing', 'off') == 'on'

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

        return flask.redirect('/base/parent_mcdi/_thanks')

    else:

        child_id_filter = models.Filter(
            "child_id",
            "eq",
            parent_form.database_id
        )
        results = filter_util.run_search_query([child_id_filter], "snapshots")
        results.sort(key=lambda x: x.session_date, reverse=True)
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
