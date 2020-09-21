"""Logic for managing consent forms.

Logic for rendering rendering views and responding to requests related to
querying the database and producing CSV files and zip archives.

Copyright (C) 2020 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

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
import csv
import datetime
import io
import time
import urllib.parse

import flask

from ..util import constants
from ..util import db_util
from ..util import session_util

from ..struct import models

from . import controller_types

from cdibase import app


SUCCESS_DELETE_MSG = 'Consent records deleted.'
SUCCESS_UPDATE_MSG = 'Consent settings updated for %s.'


@app.route('/base/edit_consent')
@session_util.require_login(change_formats=True)
def consent_index() -> controller_types.ValidFlaskReturnTypes:
    """Render a page which allows the user to select a study.

    @returns: Page which allows the user to specify a study for which they
        want to modify consent form settings.
    """
    studies = db_util.list_studies()
    return flask.render_template(
        'edit_consent.html',
        cur_page='edit_consent',
        studies=studies,
        **session_util.get_standard_template_values()
    )


@app.route('/base/edit_consent/delete', methods=['GET', 'POST'])
@session_util.require_login(change_formats=True, admin=True)
def delete_consent() -> controller_types.ValidFlaskReturnTypes:
    """Render a page which allows the user to delete user consent info.

    @returns: Page which allows the user to specify a study for which they
        want to modify consent form settings or redirect on delete.
    """
    if flask.request.method == 'GET':
        return flask.render_template(
            'delete_consent.html',
            cur_page='edit_consent',
            **session_util.get_standard_template_values()
        )
    else:
        email = flask.request.form['email']
        db_util.delete_consent_filings(email)
        flask.session[constants.CONFIRMATION_ATTR] = SUCCESS_DELETE_MSG
        return flask.redirect('/base/edit_consent')


@app.route('/base/edit_consent/studies/<study>', methods=['GET', 'POST'])
@session_util.require_login(change_formats=True)
def edit_consent_settings(study) -> controller_types.ValidFlaskReturnTypes:
    """Edit the consent settings for a study or go to URL for download.

    @param study: The name of the study.
    @returns: Page which allows the user to edit study settings or redirect
        on update. Note will give 404 if study is not known.
    """
    studies = db_util.list_studies()
    if not study in studies:
        return 'Unknown study name.', 404

    if flask.request.method == 'GET':
        return flask.render_template(
            'edit_consent_form.html',
            cur_page='edit_consent',
            cur_settings=db_util.get_consent_settings(study),
            study=study,
            **session_util.get_standard_template_values()
        )
    else:
        requirement_type_str = flask.request.form['requirement_type']
        form_content = flask.request.form['form_content']
        other_options_str = flask.request.form['other_options']
        updated = datetime.datetime.utcnow()

        requirement_type_int = int(requirement_type_str)
        assert requirement_type_int in [
            constants.CONSENT_FORM_NONE,
            constants.CONSENT_FORM_ALWAYS,
            constants.CONSENT_FORM_ONCE
        ]

        other_options_raw = other_options_str.split('\n')
        other_options_stripped = map(lambda x: x.strip(), other_options_raw)
        other_options_clean = filter(lambda x: x != '', other_options_stripped)
        other_options_list = list(other_options_clean)

        new_model = models.ConsentFormSettings(
            study,
            requirement_type_int,
            form_content,
            other_options_list,
            updated
        )
        db_util.put_consent_settings(new_model)

        msg = SUCCESS_UPDATE_MSG % study
        flask.session[constants.CONFIRMATION_ATTR] = msg

        return flask.redirect('/base/edit_consent')


@app.route('/base/edit_consent/studies/<study>/download')
@session_util.require_login(change_formats=True, admin=True)
def get_study_consent_filed(study) -> controller_types.ValidFlaskReturnTypes:
    """Get the completed consent information.

    @param study: The name of the study.
    @returns: CSV rendering of the consent data.
    """
    studies = db_util.list_studies()
    if not study in studies:
        return 'Unknown study name.', 404

    filings = db_util.get_consent_filings(study)
    filings_dicts = map(lambda x: {
        'study': x.study,
        'name': x.name,
        'child_id': x.child_id,
        'completed': x.completed.isoformat(),
        'other_options': '\n'.join(x.other_options),
        'email': x.email,
        'access_key': x.access_key
    }, filings)

    field_names = [
        'study',
        'name',
        'child_id',
        'completed',
        'other_options',
        'email',
        'access_key'
    ]

    output_io = io.StringIO()
    writer = csv.DictWriter(output_io, fieldnames=field_names)
    writer.writeheader()
    writer.writerows(filings_dicts)

    output = flask.make_response(output_io.getvalue())
    disposition = 'attachment; filename=consent%s.csv' % urllib.parse.quote(
        study
    )
    output.headers['Content-Disposition'] = disposition
    output.headers['Content-type'] = 'text/csv'

    return output
