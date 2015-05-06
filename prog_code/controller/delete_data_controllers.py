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
from ..util import user_util
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
INVALID_CONFIRM_CREDENTIALS_MSG = 'The password you entered was incorrect. ' \
    'Please enter your account password again to confirm this delete operation.'
PLEASE_CONFIRM_MESSAGE = 'Please confirm this delete operation by entering ' \
    'your password.'
DELETED_MESSAGE = 'Entries deleted.'
RESTORED_MESSAGE = 'Entries restored.'
NEED_OPERATION_MSG = 'Please specify if you want to delete or restore ' \
    'matching entries.'

CONTENT_DISPOISTION_ZIP = 'attachment; filename=mcdi_results.zip'
CONTENT_DISPOISTION_CSV = 'attachment; filename=mcdi_results.csv'
CSV_MIME_TYPE = 'text/csv'
OCTET_MIME_TYPE = 'application/octet-stream'

DELETE_DATA_URL = '/base/delete_data'
EXECUTE_URL = '/base/delete_data/execute?operation=%s'

DELETE_WAITING_ATTR = 'is_waiting_delete'
ERROR_ATTR = constants.ERROR_ATTR
PASSWORD_ATTR = 'password'
OPERATION_ATTR = 'operation'

DELETE_OPERATION = 'delete'
RESTORE_OPERATION = 'restore'

FORMAT_SESSION_ATTR = constants.FORMAT_SESSION_ATTR
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR

SNAPSHOTS_DB_TABLE = constants.SNAPSHOTS_DB_TABLE

HTML_CHECKBOX_SELECTED = 'on'


@app.route('/base/delete_data')
@session_util.require_login(delete_data=True)
def delete_data():
    """Index page for building database queries.

    @return: Listing of available CSV rendering "formats" 
    @rtype: flask.Response
    """
    return flask.render_template(
        'delete_data.html',
        cur_page='delete_data',
        formats=db_util.read_presentation_model_listing(),
        filters=map(interp_util.filter_to_str, session_util.get_filters()),
        **session_util.get_standard_template_values()
    )


@app.route('/base/delete_data/delete_mcdi_results', methods=['POST'])
@session_util.require_login(delete_data=True)
def start_delete_request():
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
    password = flask.request.form.get(PASSWORD_ATTR, '')
    confirm = user_util.check_user_password(
        session_util.get_user_email(),
        password
    )
    if not confirm:
        flask.session[ERROR_ATTR] = INVALID_CONFIRM_CREDENTIALS_MSG
        return flask.redirect(DELETE_DATA_URL)

    operation_str = flask.request.form.get(OPERATION_ATTR, '')
    if not operation_str in [DELETE_OPERATION, RESTORE_OPERATION]:
        flask.session[ERROR_ATTR] = NEED_OPERATION_MSG
        return flask.redirect(DELETE_DATA_URL)

    session_util.set_waiting_on_delete(True)
    flask.session[FORMAT_SESSION_ATTR] = flask.request.args.get(
        FORMAT_SESSION_ATTR, '')
    
    return flask.redirect(EXECUTE_URL % operation_str)


@app.route('/base/delete_data/is_waiting')
@session_util.require_login(delete_data=True)
def is_waiting_on_delete():
    """Determine if the user is waiting on a delete to start.

    Determine if a user is waiting for CSV file contents to be generated in
    response to an MCDI database query.

    @return: JSON serialization of the status of the delete. Will be a
        serialization of an JS-object with the single attribute: is_waiting
        that will have a boolean value of true or false.
    @rtype: str
    """
    ret_val = {DELETE_WAITING_ATTR: session_util.is_waiting_on_delete()}
    return json.dumps(ret_val)


@app.route('/base/delete_data/add_filter', methods=['POST'])
@session_util.require_login(delete_data=True)
def add_filter_from_delete():
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
        return flask.redirect(DELETE_DATA_URL)
    if operator == None:
        flask.session[ERROR_ATTR] = OPERATOR_NOT_SPECIFIED_MSG
        return flask.redirect(DELETE_DATA_URL)
    if operand == None:
        flask.session[ERROR_ATTR] = OPERAND_NOT_SPECIFIED_MSG
        return flask.redirect(DELETE_DATA_URL)

    # Create new filter
    new_filter = models.Filter(field, operator, operand)
    session_util.add_filter(new_filter)

    #flask.session[CONFIRMATION_ATTR] = FILTER_CREATED_MSG
    flask.session['scroll'] = True
    return flask.redirect(DELETE_DATA_URL)


@app.route('/base/delete_data/delete_filter/<int:filter_index>')
@session_util.require_login(delete_data=True)
def delete_filter_from_delete(filter_index):
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
        return flask.redirect(DELETE_DATA_URL)
    else:
        flask.session[ERROR_ATTR] = FILTER_ALREADY_DELETED_MSG
        return flask.redirect(DELETE_DATA_URL)


@app.route('/base/delete_data/execute')
@session_util.require_login(delete_data=True)
def execute_delete_request():
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
    operation = request.args.get('operation', RESTORE_OPERATION)

    if not session_util.is_waiting_on_delete():
        flask.session[ERROR_ATTR] = PLEASE_CONFIRM_MESSAGE
        return flask.redirect(DELETE_DATA_URL)

    if not session_util.get_filters():
        session_util.set_waiting_on_delete(False)
        flask.session[ERROR_ATTR] = NO_FILTER_MESSAGE
        return flask.redirect(DELETE_DATA_URL)

    snapshots = filter_util.run_delete_query(
        session_util.get_filters(),
        SNAPSHOTS_DB_TABLE,
        operation == RESTORE_OPERATION
    )

    if operation == RESTORE_OPERATION:
        flask.session[CONFIRMATION_ATTR] = RESTORED_MESSAGE
    else:
        flask.session[CONFIRMATION_ATTR] = DELETED_MESSAGE
    session_util.set_waiting_on_delete(False)
    return flask.redirect(DELETE_DATA_URL)
