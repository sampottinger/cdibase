"""Driver for the DaxlabBase web application / database manager

@author: Sam Pottinger
@license: GNU GPL v2
"""

import flask

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

@app.route("/base")
def main():
    """Controller for the daxlabbase homepage.

    @return: Rendered version of the DaxlabBase homepage.
    @rtype: flask.Response
    """
    return flask.render_template(
        "home.html",
        cur_page="home",
        **session_util.get_standard_template_values()
    )
