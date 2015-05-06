"""Logic for rendering views / responding to requests related to data download.

Logic for rendering rendering views and responding to requests related to
querying the database and producing CSV files and zip archives.

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

import flask

from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import interp_util
from ..util import report_util
from ..util import session_util

from ..struct import models

from daxlabbase import app

NO_FILTER_MESSAGE = 'No filters selected! Please add at least one filter.'
NO_MATCHING_DATA_MSG = 'No matching data found.'
FIELD_NOT_SPECIFIED_MSG = 'Field not specified. Please try again.'
OPERATOR_NOT_SPECIFIED_MSG = 'Operator not specified. Please try again.'
OPERAND_NOT_SPECIFIED_MSG = 'Operand not specified. Please try again.'
FILTER_CREATED_MSG = 'Filter created.'
FILTER_DELETED_MSG = 'Filter deleted.'
FILTER_ALREADY_DELETED_MSG = 'Filter already deleted.'
UNKNOWN_PRESENTATION_FORMAT_MSG = 'Unknown presentation format specified.'

CONTENT_DISPOISTION_ZIP = 'attachment; filename=mcdi_results.zip'
CONTENT_DISPOISTION_CSV = 'attachment; filename=mcdi_results.csv'
CSV_MIME_TYPE = 'text/csv'
OCTET_MIME_TYPE = 'application/octet-stream'

CONSOLIDATED_FILE_URL = '/base/access_data/download_mcdi_results.csv?deleted=%s'
ARCHIVE_FILE_URL = '/base/access_data/download_mcdi_results.zip?deleted=%s'
ACCESS_DATA_URL = '/base/access_data'

DOWNLOAD_WAITING_ATTR = 'is_waiting'
ERROR_ATTR = constants.ERROR_ATTR

FORMAT_SESSION_ATTR = constants.FORMAT_SESSION_ATTR
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR

SNAPSHOTS_DB_TABLE = constants.SNAPSHOTS_DB_TABLE

HTML_CHECKBOX_SELECTED = 'on'


@app.route('/base/access_data')
@session_util.require_login(access_data=True)
def access_data():
    """Index page for building database queries.

    @return: Listing of available CSV rendering "formats" 
    @rtype: flask.Response
    """
    formats = list(db_util.read_presentation_model_listing())
    formats.reverse()
    return flask.render_template(
        'access_data.html',
        cur_page='access_data',
        formats=formats,
        filters=map(interp_util.filter_to_str, session_util.get_filters()),
        studies=db_util.list_studies(),
        **session_util.get_standard_template_values()
    )


@app.route('/base/access_data/download_mcdi_results', methods=['POST'])
@session_util.require_login(access_data=True)
def execute_access_request():
    """Execute a MCDI database query and download the results.

    Execute an MCDI database query queued in a user's session and return the
    results in either a single "consolidated" CSV or a zip archive of CSVs. The
    request should include format as an argument indicating the presentation 
    format that the MCDIs should be provided in (name of a presentation format
    provided via configuration file) as it will be saved to the session and
    used by execute_zip_access_request. The request should also include
    a consolidated_csv argument that, if equal to "on" will have the requset
    redirected to the single consolidated CSV URL.

    @return: Redirect
    @rtype: flask.redirect
    """
    session_util.set_waiting_on_download(True)
    flask.session[FORMAT_SESSION_ATTR] = flask.request.form.get(
        FORMAT_SESSION_ATTR, '')

    use_consolidated = flask.request.form.get(
        'consolidated_csv',
        ''
    )

    include_deleted_str = flask.request.form.get(
        'deleted',
        'ignore'
    )
    
    if use_consolidated == HTML_CHECKBOX_SELECTED:
        return flask.redirect(CONSOLIDATED_FILE_URL % include_deleted_str)
    else:
        return flask.redirect(ARCHIVE_FILE_URL % include_deleted_str)


@app.route('/base/access_data/is_waiting')
@session_util.require_login(access_data=True)
def is_waiting_on_download():
    """Determine if the user is waiting on a download to start.

    Determine if a user is waiting for CSV file contents to be generated in
    response to an MCDI database query.

    @return: JSON serialization of the status of the download. Will be a
        serialization of an JS-object with the single attribute: is_waiting
        that will have a boolean value of true or false.
    @rtype: str
    """
    ret_val = {DOWNLOAD_WAITING_ATTR: session_util.is_waiting_on_download()}
    return json.dumps(ret_val)


@app.route('/base/access_data/abort')
@session_util.require_login(access_data=True)
def abort_download():
    """Have the session indicate that the user gave up on waiting for download.

    Have the user's session indicate that the user decided not to wait for CSV
    file contents to be generated from an MCDI database query.

    @return: JSON serialization of the updated status of the user's download.
        Will be a serialization of an JS-object with the single attribute:
        is_waiting that will have a boolean value of true or false. If aborted
        successfully, this attribute will be false.
    @rtype: str
    """
    session_util.set_waiting_on_download(False)
    ret_val = {DOWNLOAD_WAITING_ATTR: session_util.is_waiting_on_download()}
    return json.dumps(ret_val)


@app.route('/base/access_data/distribution')
@session_util.require_login(access_data=True)
def get_study_distribution():
    """Get a JSON file describing how many CDIs there are per study.

    @return: JSON serialization of CDI frequency distribution.
    @rtype: str
    """
    return json.dumps(db_util.get_counts())


@app.route('/base/access_data/add_filter', methods=['POST'])
@session_util.require_login(access_data=True)
def add_filter():
    """Controller to add a filter to the query the user is currently building.

    Controller that adds an additional AND clause to the query the user is
    currently building against the database. Should include field, operator,
    and operand form values. If not included, this will return a redirect
    to the user query building form after indicating an error in the user
    session. If successful, this will add a confirmation message to the user
    session and redirect to the same form.

    @return: Redirect
    @rtype: flask.Response
    """
    request = flask.request

    # Parse options
    field = request.form.get('field', None)
    operator = request.form.get('operator', None)
    operand = request.form.get('operand', None)

    # Check correct fields provided
    if field == None:
        flask.session[ERROR_ATTR] = FIELD_NOT_SPECIFIED_MSG
        return flask.redirect(ACCESS_DATA_URL)
    if operator == None:
        flask.session[ERROR_ATTR] = OPERATOR_NOT_SPECIFIED_MSG
        return flask.redirect(ACCESS_DATA_URL)
    if operand == None:
        flask.session[ERROR_ATTR] = OPERAND_NOT_SPECIFIED_MSG
        return flask.redirect(ACCESS_DATA_URL)

    # Create new filter
    new_filter = models.Filter(field, operator, operand)
    session_util.add_filter(new_filter)

    #flask.session[CONFIRMATION_ATTR] = FILTER_CREATED_MSG
    flask.session['scroll'] = True
    return flask.redirect(ACCESS_DATA_URL)


@app.route('/base/access_data/delete_filter/<int:filter_index>')
@session_util.require_login(access_data=True)
def delete_filter(filter_index):
    """Controller to delete a filter from query the user is currently building.

    Controller that removes an AND clause from the query the user is currently
    building against the database. Will set either an error or a conformation
    message in the user session.
    
    @param filter_index: The numerical index of filter to be deleted. Index goes
        to element in list of filters for user's current query.
    @type filter_index: int
    @return: Redirect
    @rtype: flask.Response
    """
    if session_util.delete_filter(filter_index):
        #flask.session[CONFIRMATION_ATTR] = FILTER_DELETED_MSG
        flask.session['scroll'] = True
        return flask.redirect(ACCESS_DATA_URL)
    else:
        flask.session[ERROR_ATTR] = FILTER_ALREADY_DELETED_MSG
        return flask.redirect(ACCESS_DATA_URL)


@app.route('/base/access_data/download_mcdi_results.zip')
@session_util.require_login(access_data=True)
def execute_zip_access_request():
    """Controller for finding and rendering archive of database query results.

    Controller that executes a request (that must have atleast one filter) using
    the selected filters and the selected format. Will also reset the waiting
    on download flag. Will reject with an error message saved to the user
    session if no filters are supplied, an invalid format is specified, or
    no data is available.

    @return: ZIP archive where each study with results has a CSV file.
    @rtype: flask.Response
    """
    request = flask.request

    if not session_util.get_filters():
        session_util.set_waiting_on_download(False)
        flask.session[ERROR_ATTR] = NO_FILTER_MESSAGE
        return flask.redirect(ACCESS_DATA_URL)

    snapshots = filter_util.run_search_query(
        session_util.get_filters(),
        SNAPSHOTS_DB_TABLE,
        request.args.get('deleted', 'ignore') == 'ignore'
    )

    if len(snapshots) == 0:
        session_util.set_waiting_on_download(False)
        flask.session[ERROR_ATTR] = NO_MATCHING_DATA_MSG
        return flask.redirect(ACCESS_DATA_URL)

    pres_format_name = flask.session[FORMAT_SESSION_ATTR]
    presentation_format = db_util.read_presentation_model(pres_format_name)
    if presentation_format == None:
        session_util.set_waiting_on_download(False)
        flask.session[ERROR_ATTR] = UNKNOWN_PRESENTATION_FORMAT_MSG
        return flask.redirect(ACCESS_DATA_URL)

    zip_file = report_util.generate_study_report(snapshots, presentation_format)
    zip_contents = zip_file.getvalue()

    response = flask.Response(
        zip_contents,
        mimetype=OCTET_MIME_TYPE
    )
    response.headers['Content-Type'] = OCTET_MIME_TYPE
    response.headers['Content-Disposition'] = CONTENT_DISPOISTION_ZIP
    response.headers['Content-Length'] = len(zip_contents)

    session_util.set_waiting_on_download(False)
    return response


@app.route('/base/access_data/download_mcdi_results.csv')
@session_util.require_login(access_data=True)
def execute_csv_access_request():
    """Controller for finding and rendering archives of database query results.

    @return: ZIP archive where each study with results has a CSV file.
    @rtype: flask.Response
    """
    request = flask.request

    if not session_util.get_filters():
        session_util.set_waiting_on_download(False)
        flask.session[ERROR_ATTR] = NO_FILTER_MESSAGE
        return flask.redirect(ACCESS_DATA_URL)

    snapshots = filter_util.run_search_query(
        session_util.get_filters(),
        SNAPSHOTS_DB_TABLE,
        request.args.get('deleted', 'ignore') == 'ignore'
    )

    if len(snapshots) == 0:
        session_util.set_waiting_on_download(False)
        flask.session[ERROR_ATTR] = NO_MATCHING_DATA_MSG
        return flask.redirect(ACCESS_DATA_URL)

    pres_format_name = flask.session[FORMAT_SESSION_ATTR]
    presentation_format = db_util.read_presentation_model(pres_format_name)
    if presentation_format == None:
        session_util.set_waiting_on_download(False)
        flask.session[ERROR_ATTR] = UNKNOWN_PRESENTATION_FORMAT_MSG
        return flask.redirect(ACCESS_DATA_URL)

    csv_file = report_util.generate_consolidated_study_report(snapshots,
        presentation_format)
    csv_contents = csv_file.getvalue()

    response = flask.Response(
        csv_contents,
        mimetype=CSV_MIME_TYPE
    )
    response.headers['Content-Type'] = CSV_MIME_TYPE
    response.headers['Content-Disposition'] = CONTENT_DISPOISTION_CSV
    response.headers['Content-Length'] = len(csv_contents)

    session_util.set_waiting_on_download(False)
    return response
