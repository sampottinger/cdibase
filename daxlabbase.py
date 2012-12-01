import os
import urllib

import flask

import models
import util
import db_util
import file_util
import filter_util
import math_util
import report_util
import session_util
import constants

app = flask.Flask(__name__)
app.debug = True
app.config['UPLOAD_FOLDER'] = file_util.UPLOAD_FOLDER
app.secret_key = '\xd1\xaa\'S\xba\x90^&\xb4f2\xf9"\xc7U\x06\xc2\xff\xae\x7f\xaf\x83h\xd9'

@app.route("/")
def main():
    return flask.render_template("home.html", cur_page="home")

@app.route("/enter_data")
def enter_data_intro():
    return flask.render_template(
        "enter_data.html",
        cur_page="enter_data",
        formats=db_util.load_mcdi_model_listing(),
        error=session_util.get_error(),
        confirmation=session_util.get_confirmation()
    )

@app.route("/enter_data/<format_name>", methods=["GET", "POST"])
def enter_data_form(format_name):
    request = flask.request

    format = db_util.load_mcdi_model(format_name)
    if format == None:
        flask.session["error"] = "Could not the specified MCDI format."
        return flask.redirect("/enter_data")

    # Render form
    if request.method == "GET":
        return flask.render_template(
            "enter_data_form.html",
            cur_page="enter_data",
            format=format,
            error=session_util.get_error(),
            confirmation=session_util.get_confirmation()
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
            gender = util.safe_int_interpret(gender)
            if gender == None:
                error = "gender value was invalid."

        if age == "":
            error = "age was empty."
        else:
            age = util.safe_float_interpret(age)
            if age == None:
                error = "participant age should be a number."

        if birthday == "":
            error = "birthday was empty."

        if session_date == "":
            error = "session_date was empty."

        if session_num == "":
            error = "session_num was empty."
        else:
            session_num = util.safe_int_interpret(session_num)
            if session_num == None:
                error = "session number should be a whole number."

        if items_excluded == "":
            error = "items excluded was empty."
        else:
            items_excluded = util.safe_int_interpret(items_excluded)
            if items_excluded == None:
                error = "items excluded should be a whole number."

        if extra_categories == "":
            error = "extra categories was empty."
        else:
            extra_categories = util.safe_int_interpret(extra_categories)
            if extra_categories == None:
                error = "extra categories should be a whole number."

        if total_num_sessions == "":
            error = "total number sessions was empty."
        else:
            total_num_sessions = util.safe_int_interpret(total_num_sessions)
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

        flask.session["confirmation"] = "MCDI record added for participant %d." % global_id

        return flask.redirect(request.path)

@app.route("/edit_formats")
def edit_formats():
    return flask.render_template(
        "edit_formats.html",
        cur_page="edit_formats",
        mcdi_formats=db_util.load_mcdi_model_listing(),
        presentation_formats=db_util.load_presentation_model_listing(),
        percentile_tables=db_util.load_percentile_model_listing(),
        error=session_util.get_error(),
        confirmation=session_util.get_confirmation()
    )

@app.route("/access_data")
def access_data():
    return flask.render_template(
        "access_data.html",
        cur_page="access_data",
        formats=db_util.load_presentation_model_listing(),
        filters=map(util.filter_to_str, session_util.get_filters()),
        error=session_util.get_error(),
        confirmation=session_util.get_confirmation()
    )

@app.route("/access_data/download_mcdi_results.zip")
def execute_access_request():
    request = flask.request

    if not session_util.get_filters():
        flask.session["error"] = "No filters selected! Please add atleast one filter."
        return flask.redirect("/access_data")

    snapshots = filter_util.run_search_query(
        session_util.get_filters(),
        "snapshots"
    )

    if len(snapshots) == 0:
        flask.session["error"] = "No matching data found."
        return flask.redirect("/access_data")

    # TODO: Handle unknown format
    pres_format_name = request.args["format"]
    presentation_format = db_util.load_presentation_model(pres_format_name)

    zip_file = report_util.generate_study_report(snapshots, presentation_format)

    return flask.Response(
        zip_file.getvalue(),
        mimetype="application/octet-stream"
    )

@app.route("/access_data/add_filter", methods=["POST"])
def add_filter():
    request = flask.request

    # Parse options
    field = request.form.get("field", None)
    operator = request.form.get("operator", None)
    operand = request.form.get("operand", None)

    # Check correct fields provided
    if field == None:
        flask.session["error"] = "Field not specified. Please try again."
        return flask.redirect("/access_data")
    if operator == None:
        flask.session["error"] = "Operator not specified. Please try again."
        return flask.redirect("/access_data")
    if operand == None:
        flask.session["error"] = "Operand not specified. Please try again."
        return flask.redirect("/access_data")

    # Create new filter
    new_filter = models.Filter(field, operator, operand)
    session_util.add_filter(new_filter)

    flask.session["confirmation"] = "Filter created."
    return flask.redirect("/access_data")

@app.route("/access_data/delete_filter/<int:filter_index>")
def delete_filter(filter_index):
    if session_util.delete_filter(filter_index):
        flask.session["confirmation"] = "Filter deleted."
        return flask.redirect("/access_data")
    else:
        flask.session["error"] = "Filter already deleted."
        return flask.redirect("/access_data")

@app.route("/mcdi_format/_add", methods=["GET", "POST"])
def upload_mcdi_format():
    request = flask.request

    # Show form on browser vising page with GET
    if request.method == "GET":
        return flask.render_template(
            "upload_format.html",
            cur_page="edit_formats",
            upload_type="MCDI",
            error=session_util.get_error()
        )

    # Safe file and add record to db
    elif request.method == "POST":
        name = request.form.get("name", "")
        file = request.files["newfile"]

        if name == "":
            flask.session["error"] = "Name not specified. Please try again."
            return flask.redirect("/mcdi_format/_add")

        safe_name = name.replace(" ", "")
        safe_name = urllib.quote_plus(safe_name)

        if db_util.load_mcdi_model(safe_name) != None:
            flask.session["error"] = "Format \"%s\" already exists." % name
            return flask.redirect("/edit_formats")

        # Check file upload valid
        if file and file_util.allowed_file(file.filename):
            
            # Generate random filename
            filename = file_util.generate_unique_filename(".yaml")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            
            # Create and save record
            new_model = models.MCDIFormatMetadata(name, safe_name, filename)
            db_util.save_mcdi_model(new_model)
            
            flask.session["confirmation"] = "Format added."
            return flask.redirect("/edit_formats")

    flask.session["error"] = "File upload failed. Please try again."
    return flask.redirect("/edit_formats")

@app.route("/mcdi_format/<format_name>/delete")
def delete_mcdi_format(format_name):
    format_model = db_util.load_mcdi_model(format_name)
    if format_model == None:
        flask.session["error"] = "Could not find format. Possibly already deleted."
        return flask.redirect("/edit_formats")

    filename = os.path.join(app.config["UPLOAD_FOLDER"], format_model.filename)
    os.remove(filename)
    db_util.delete_mcdi_model(format_model)

    flask.session["confirmation"] = "Format deleted."
    return flask.redirect("/edit_formats")

@app.route("/presentation_format/_add", methods=["GET", "POST"])
def upload_presentation_format():
    request = flask.request

    # Show form on browser vising page with GET
    if request.method == "GET":
        return flask.render_template(
            "upload_format.html",
            cur_page="edit_formats",
            upload_type="Presentation",
            error=session_util.get_error()
        )

    # Safe file and add record to db
    elif request.method == "POST":
        name = request.form.get("name", "")
        file = request.files["newfile"]

        if name == "":
            flask.session["error"] = "Name not specified. Please try again."
            return flask.redirect("/presentation_format/_add")

        safe_name = name.replace(" ", "")
        safe_name = urllib.quote_plus(safe_name)

        if db_util.load_presentation_model(safe_name) != None:
            flask.session["error"] = "Format \"%s\" already exists." % name
            return flask.redirect("/edit_formats")

        # Check file upload valid
        if file and file_util.allowed_file(file.filename):
            
            # Generate random filename
            filename = file_util.generate_unique_filename(".yaml")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            
            # Create and save record
            new_model = models.PresentationFormatMetadata(name, safe_name, filename)
            db_util.save_presentation_model(new_model)
            
            flask.session["confirmation"] = "Format added."
            return flask.redirect("/edit_formats")

    flask.session["error"] = "File upload failed. Please try again."
    return flask.redirect("/edit_formats")

@app.route("/presentation_format/<format_name>/delete")
def delete_presentation_format(format_name):
    format_model = db_util.load_presentation_model(format_name)
    if format_model == None:
        flask.session["error"] = "Could not find format. Possibly already deleted."
        return flask.redirect("/edit_formats")

    filename = os.path.join(app.config["UPLOAD_FOLDER"], format_model.filename)
    os.remove(filename)
    db_util.delete_presentation_model(format_model)

    flask.session["confirmation"] = "Format deleted."
    return flask.redirect("/edit_formats")

@app.route("/percentile_table/_add", methods=["GET", "POST"])
def upload_percentile_table():
    request = flask.request

    # Show form on browser vising page with GET
    if request.method == "GET":
        return flask.render_template(
            "upload_format.html",
            cur_page="edit_formats",
            upload_type="Percentile",
            error=session_util.get_error()
        )

    # Safe file and add record to db
    elif request.method == "POST":
        name = request.form.get("name", "")
        file = request.files["newfile"]

        if name == "":
            flask.session["error"] = "Name not specified. Please try again."
            return flask.redirect("/percentile_table/_add")

        safe_name = name.replace(" ", "")
        safe_name = urllib.quote_plus(safe_name)

        if db_util.load_percentile_model(safe_name) != None:
            flask.session["error"] = "Percentile table \"%s\" already exists." % name
            return flask.redirect("/edit_formats")

        # Check file upload valid
        if file and file_util.allowed_file(file.filename):
            
            # Generate random filename
            filename = file_util.generate_unique_filename(".csv")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            
            # Create and save record
            new_model = models.PercentileTableMetadata(name, safe_name, filename)
            db_util.save_percentile_model(new_model)
            
            flask.session["confirmation"] = "Percentile table added."
            return flask.redirect("/edit_formats")

    flask.session["error"] = "File upload failed. Please try again."
    return flask.redirect("/edit_formats")

@app.route("/percentile_table/<format_name>/delete")
def delete_percentile_table(format_name):
    format_model = db_util.load_percentile_model(format_name)
    if format_model == None:
        flask.session["error"] = "Could not find percentile table. Possibly already deleted."
        return flask.redirect("/edit_formats")

    filename = os.path.join(app.config["UPLOAD_FOLDER"], format_model.filename)
    os.remove(filename)
    db_util.delete_percentile_model(format_model)

    flask.session["confirmation"] = "Percentile table deleted."
    return flask.redirect("/edit_formats")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return flask.send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run()