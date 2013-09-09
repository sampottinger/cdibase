"""Logic for managing parent accounts.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import datetime
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


@app.route("/base/parent_accounts", methods=["GET", "POST"])
@session_util.require_login(edit_parents=True)
def edit_parent_accounts():
    request = flask.request
    if request.method == "POST":
        form_id = parent_account_util.generate_unique_mcdi_form_id()
        global_id = interp_util.safe_int_interpret(
            request.form.get("global_id"))
        study_id = request.form.get("study_id")
        study = request.form.get("study")
        gender = interp_util.safe_int_interpret(request.form.get("gender"))
        birthday = request.form.get("birthday")
        items_excluded = interp_util.safe_int_interpret(
            request.form.get("items_excluded"))
        extra_categories = interp_util.safe_int_interpret(
            request.form.get("extra_categories"))
        languages = request.form.get("languages")
        languages = languages.split(",")
        hard_of_hearing = request.form.get("hard_of_hearing") == "on"
        child_name = request.form.get("child_name")
        parent_email = request.form.get("parent_email")
        mcdi_type = request.form.get("mcdi_type")

        if parent_email == "":
            flask.session["error"] = "Parent email required."
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
            ",".join(languages),
            len(languages),
            hard_of_hearing
        )

        resolver = parent_account_util.AttributeResolutionResolver()
        resolver.fill_parent_form_defaults(new_form)

        db_util.insert_parent_form(new_form)
        parent_account_util.send_mcdi_email(new_form)

        flask.session["confirmation"] = "MCDI form sent."

        return flask.redirect('/base/parent_accounts')

    else:
        return flask.render_template(
            "parent_accounts.html",
            cur_page="edit_parents",
            users=user_util.get_all_users(),
            mcdi_formats=db_util.load_mcdi_model_listing(),
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
            languages = request.form['languages'].split(',')
        
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
            percentile_model = db_util.load_percentile_model(percentile_table_name)
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
