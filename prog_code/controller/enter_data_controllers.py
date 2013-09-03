"""Logic for rendering views and responding to requests related to data entry.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import flask

from ..util import db_util
from ..util import interp_util
from ..util import math_util
from ..util import session_util
from ..util import user_util

from daxlabbase import app


NOT_FOUND_MSG = "[ not found ]"


@app.route("/base/enter_data")
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
        "enter_data.html",
        cur_page="enter_data",
        formats=db_util.load_mcdi_model_listing(),
        **session_util.get_standard_template_values()
    )


@app.route("/base/enter_data/<format_name>", methods=["GET", "POST"])
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
        flask.session["error"] = "Could not the specified MCDI format."
        return flask.redirect("/base/enter_data")

    # Render form
    if request.method == "GET":
        return flask.render_template(
            "enter_data_form.html",
            cur_page="enter_data",
            selected_format=selected_format,
            formats=db_util.load_mcdi_model_listing(),
            **session_util.get_standard_template_values()
        )

    # Add new data
    elif request.method == "POST":

        # Snaptshot metadata form data
        global_id = request.form.get("global_id", "")
        study_id = request.form.get("study_id", "")
        study = request.form.get("study", "")
        gender = request.form.get("gender", "")
        age = request.form.get("age", "")
        birthday = request.form.get("birthday", "")
        session_date = request.form.get("session_date", "")
        session_num = request.form.get("session_num", "")
        items_excluded = request.form.get("items_excluded", "")
        extra_categories = request.form.get("extra_categories", "")
        total_num_sessions = request.form.get("total_num_sessions", "")
        hard_of_hearing = request.form.get("hard_of_hearing", "off") == "on"

        # Check inclusion and interpret submission
        error = None
        if global_id == "":
            error = "participant global id was empty."
        else:
            global_id = util.safe_int_interpret(global_id)
            if global_id == None:
                error = "participant global id should be a whole number."
        
        if study_id == "":
            error = "study id was empty."

        if study == "":
            error = "study was empty."

        if gender == "":
            error = "gender was empty."
        else:
            gender = interp_util.safe_int_interpret(gender)
            if gender == None:
                error = "gender value was invalid."

        if age == "":
            error = "age was empty."
        else:
            age = interp_util.safe_float_interpret(age)
            if age == None:
                error = "participant age should be a number."

        if birthday == "":
            error = "birthday was empty."

        if session_date == "":
            error = "session_date was empty."

        if session_num == "":
            error = "session_num was empty."
        else:
            session_num = interp_util.safe_int_interpret(session_num)
            if session_num == None:
                error = "session number should be a whole number."

        if items_excluded == "":
            error = "items excluded was empty."
        else:
            items_excluded = interp_util.safe_int_interpret(items_excluded)
            if items_excluded == None:
                error = "items excluded should be a whole number."

        if extra_categories == "":
            error = "extra categories was empty."
        else:
            extra_categories = interp_util.safe_int_interpret(extra_categories)
            if extra_categories == None:
                error = "extra categories should be a whole number."

        if total_num_sessions == "":
            error = "total number sessions was empty."
        else:
            total_num_sessions = interp_util.safe_int_interpret(
                total_num_sessions)
            if total_num_sessions == None:
                error = "total number sessions should be a whole number."

        if error:
            flask.session["error"] = error
            return flask.redirect(request.path)

        revision = 0

        # Parse word entries
        languages = set()
        count_as_spoken_vals = format.details["count_as_spoken"]
        word_entries = {}
        words_spoken = 0
        total_possible_words = 0
        for category in format.details["categories"]:
            languages.add(category["language"])
            for word in category["words"]:
                word_val = request.form.get("%s_report" % word, None)
                if word_val == None:
                    flask.session["error"] = "%s value missing" % word
                    return flask.redirect(request.path)
                word_val = util.safe_int_interpret(word_val)
                if word_val == None:
                    flask.session["error"] = "%s value invalid" % word
                    return flask.redirect(request.path)
                word_entries[word] = int(word_val)
                if word_val in count_as_spoken_vals:
                    words_spoken += 1
                total_possible_words += 1

        # Determine approach percentiles
        if gender == constants.MALE:
            percentile_table_name = format.details["percentiles"]["male"]
        elif gender == constants.FEMALE:
            percentile_table_name = format.details["percentiles"]["female"]
        else:
            percentile_table_name = format.details["percentiles"]["other"]

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

        connection = db_util.get_db_connection()
        cursor = connection.cursor()

        # Put in snapshot metadata
        cmd = "INSERT INTO snapshots VALUES (%s)" % (", ".join("?" * 19))
        cursor.execute(
            cmd,
            (
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
                ",".join(languages),
                len(languages),
                format.details["meta"]["mcdi_type"],
                hard_of_hearing
            )
        )
        new_snapshot_id = cursor.lastrowid

        # Put in snapshot contents
        for (word, val) in word_entries.items():
            cursor.execute(
                "INSERT INTO snapshot_content VALUES (?, ?, ?, ?)",
                (
                    new_snapshot_id,
                    word,
                    val,
                    0
                )
            )

        connection.commit()
        connection.close()

        flask.session["confirmation"] = "MCDI record added for participant %d." % global_id

        return flask.redirect(request.path)


@app.route("/base/enter_data/lookup_global_id/<study_name>/<participant_study_id>")
@session_util.require_login(enter_data=True)
def lookup_global_id(study_name, participant_study_id):
    global_id = db_util.lookup_global_participant_id(study_name,
        participant_study_id)
    if global_id == None:
        return flask.Response(NOT_FOUND_MSG)
    else:
        return flask.Response(str(global_id))
