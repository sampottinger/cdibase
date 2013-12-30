import io

import flask

from daxlabbase import app

from ..util import constants
from ..util import csv_import_util
from ..util import db_util
from ..util import session_util

CONFIRM_MSG = 'CSV imported into the database.'


@app.route('/base/import_data', methods=['GET', 'POST'])
@session_util.require_login(import_data=True)
def import_data():
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
        results = csv_import_util.parse_csv(
            contents,
            mcdi_type,
            ['english'],
            constants.EXPLICIT_FALSE,
            True
        )

        if results['error']:
            flask.session[constants.ERROR_ATTR] = results['error']
        else:
            flask.session[constants.CONFIRMATION_ATTR] = CONFIRM_MSG

        if mcdi_type != '':
            flask.session['last_format_used'] = mcdi_type

        return flask.redirect('/base/import_data')
