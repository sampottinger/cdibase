"""Logic for rendering and responding to user requests related to data import.

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

import io
import json

import flask

from cdibase import app

from ..util import constants
from ..util import legacy_csv_import_util
from ..util import new_csv_import_util
from ..util import db_util
from ..util import session_util

CONFIRM_MSG = 'CSV imported into the database.'


@app.route('/base/import_data', methods=['GET', 'POST'])
@session_util.require_login(import_data=True)
def import_data():
    """Controller to import a CSV file into the lab database.

    @return: Form to perform the import if GET and redirect if POST with info
        on if the import was successful.
    @rtype: flask.Response
    """
    default_format = flask.session.get(
        'last_format_used',
        db_util.load_mcdi_model_listing()[0].safe_name
    )

    if flask.request.method == 'GET':
        return flask.render_template(
            'import_data.html',
            cur_page='import_data',
            formats=db_util.load_mcdi_model_listing(),
            default_format=default_format,
            **session_util.get_standard_template_values()
        )

    else:
        contents = io.StringIO(
            unicode(flask.request.files['file'].read()), newline=None
        )
        mcdi_type = flask.request.form.get('cdi-type', '')
        file_format = flask.request.form['file-format']

        if file_format == "new":
            return import_data_new(contents)
        else:
            return import_data_legacy(contents, mcdi_type)


def import_data_new(contents):
    results = new_csv_import_util.process_csv(contents)

    if results.had_error:
        flask.session[constants.ERROR_ATTR] = results.error_msg
        return flask.redirect('/base/import_data')

    impacted_ids = []
    for record in results.records:
        db_util.insert_snapshot(record.meta, record.contents)
        impacted_ids.append(record.meta.database_id)

    db_util.report_usage(
        session_util.get_user_email(),
        "Import Data",
        json.dumps({
            "global_ids": impacted_ids
        })
    )

    flask.session[constants.CONFIRMATION_ATTR] = CONFIRM_MSG
    return flask.redirect('/base/import_data')


def import_data_legacy(contents, mcdi_type):
    results = legacy_csv_import_util.parse_csv(
        contents,
        mcdi_type,
        ['english'],
        constants.EXPLICIT_FALSE,
        True
    )

    if results['error']:
        flask.session[constants.ERROR_ATTR] = results['error']
        return flask.redirect('/base/import_data')
    else:
        flask.session[constants.CONFIRMATION_ATTR] = CONFIRM_MSG

    db_util.report_usage(
        session_util.get_user_email(),
        "Import Data",
        json.dumps({
            "global_ids": results["ids"]
        })
    )

    if mcdi_type != '':
        flask.session['last_format_used'] = mcdi_type

    return flask.redirect('/base/import_data')
