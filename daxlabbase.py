"""Driver for the DaxlabBase web application / database manager

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

# TODO(apottinger): Change to cdibase.py

import flask # type: ignore

from flask_mail import Mail

from prog_code.util import session_util
from prog_code.util import file_util
from prog_code.util import mail_util
from prog_code.util import session_util

app = flask.Flask(__name__)
app.config.from_pyfile('flask_config.cfg')
app.config['UPLOAD_FOLDER'] = file_util.UPLOAD_FOLDER
if not app.config['NO_MAIL']:
    mail_util.init_mail(app)
elif app.config['DEBUG_PRINT_EMAIL']:
    mail_util.DEBUG_PRINT_EMAIL = True

from prog_code.controller import access_data_controllers
from prog_code.controller import account_controllers
from prog_code.controller import api_key_controllers
from prog_code.controller import edit_parent_controllers
from prog_code.controller import edit_user_controllers
from prog_code.controller import enter_data_controllers
from prog_code.controller import delete_data_controllers
from prog_code.controller import format_controllers
from prog_code.controller import import_data_controllers

@app.route("/base")
def main():
    """Controller for the daxlabbase homepage.

    @return: Rendered version of the DaxlabBase homepage.
    @rtype: flask.Response
    """
    if session_util.is_logged_in():
        return flask.render_template(
            "home.html",
            cur_page="home",
            **session_util.get_standard_template_values()
        )
    else:
        return flask.render_template(
            "login_home.html",
            cur_page="home",
            **session_util.get_standard_template_values()
        )


def disable_email():
    mail_util.DEBUG_PRINT_EMAIL = False
    mail_util.disable_mail()
