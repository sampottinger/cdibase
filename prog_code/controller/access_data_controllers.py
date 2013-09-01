"""Logic for rendering views / responding to requests related to data download.

Logic for rendering rendering views and responding to requests related to
querying the database and producing CSV files and zip archives.

@author: Sam Pottinger
@license: GNU GPL v2
"""
import json

import flask

from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import report_util
from ..util import session_util

from ..struct import models

from daxlabbase import app


@app.route("/access_data")
@session_util.require_login(access_data=True)
def access_data():
    """Index page for building database queries.

    @return: Listing of available CSV rendering "formats" 
    @rtype: flask.Response
    """
    return flask.render_template(
        "access_data.html",
        cur_page="access_data",
        formats=db_util.load_presentation_model_listing(),
        filters=map(interp_util.filter_to_str, session_util.get_filters()),
        **session_util.get_standard_template_values()
    )


@app.route("/access_data/download_mcdi_results")
@session_util.require_login(access_data=True)
def execute_access_request():
    session_util.set_waiting_on_download(True)
    flask.session["format"] = flask.request.args.get("format", "")
    if flask.request.args.get("consolidated_csv", "") == "on":
        return flask.redirect("/access_data/download_mcdi_results.csv")
    else:
        return flask.redirect("/access_data/download_mcdi_results.zip")


@app.route("/access_data/is_waiting")
@session_util.require_login(access_data=True)
def is_waiting_on_download():
    ret_val = {'is_waiting': session_util.is_waiting_on_download()}
    return json.dumps(ret_val)


@app.route("/access_data/abort")
@session_util.require_login(access_data=True)
def abort_download():
    session_util.set_waiting_on_download(False)
    ret_val = {'is_waiting': session_util.is_waiting_on_download()}
    return json.dumps(ret_val)



@app.route("/access_data/download_mcdi_results.zip")
@session_util.require_login(access_data=True)
def execute_zip_access_request():
    """Controller for finding and rendering archive of database query results.

    @return: ZIP archive where each study with results has a CSV file.
    @rtype: flask.Response
    """
    request = flask.request

    if not session_util.get_filters():
        flask.session["error"] = "No filters selected! Please add at least one filter."
        return flask.redirect("/access_data")

    snapshots = filter_util.run_search_query(
        session_util.get_filters(),
        "snapshots"
    )

    if len(snapshots) == 0:
        flask.session["error"] = "No matching data found."
        return flask.redirect("/access_data")

    # TODO: Handle unknown format
    pres_format_name = flask.session["format"]
    presentation_format = db_util.load_presentation_model(pres_format_name)

    zip_file = report_util.generate_study_report(snapshots, presentation_format)
    zip_contents = zip_file.getvalue()

    response = flask.Response(
        zip_contents,
        mimetype="application/octet-stream"
    )
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename=mcdi_results.zip'
    response.headers['Content-Length'] = len(zip_contents)

    session_util.set_waiting_on_download(False)
    return response


@app.route("/access_data/download_mcdi_results.csv")
@session_util.require_login(access_data=True)
def execute_csv_access_request():
    """Controller for finding and rendering archive of database query results.

    @return: ZIP archive where each study with results has a CSV file.
    @rtype: flask.Response
    """
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
    pres_format_name = flask.session["format"]
    presentation_format = db_util.load_presentation_model(pres_format_name)

    csv_file = report_util.generate_consolidated_study_report(snapshots, presentation_format)
    csv_contents = csv_file.getvalue()

    response = flask.Response(
        csv_contents,
        mimetype="text/csv"
    )
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=mcdi_results.csv'
    response.headers['Content-Length'] = len(csv_contents)

    session_util.set_waiting_on_download(False)
    return response


@app.route("/access_data/add_filter", methods=["POST"])
@session_util.require_login(access_data=True)
def add_filter():
    """Controller to add a filter to the query the user is currently building.

    Controller that adds an additional AND clause to the query the user is
    currently building against the database.

    @return: Redirect
    @rtype: flask.Response
    """
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
@session_util.require_login(access_data=True)
def delete_filter(filter_index):
    """Controller to delete a filter from query the user is currently building.

    Controller that removes an AND clause from the query the user is currently
    building against the database.
    
    @param filter_index: The numerical index of filter to be deleted. Index goes
        to element in list of filters for user's current query.
    @type filter_index: int
    @return: Redirect
    @rtype: flask.Response
    """
    if session_util.delete_filter(filter_index):
        flask.session["confirmation"] = "Filter deleted."
        return flask.redirect("/access_data")
    else:
        flask.session["error"] = "Filter already deleted."
        return flask.redirect("/access_data")
