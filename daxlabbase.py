"""Driver for the DaxlabBase web application / database manager

@author: Sam Pottinger
@license: GNU GPL v2
"""

import os
import urllib

import flask

from werkzeug.contrib.fixers import ProxyFix

from flask_mail import Mail

from prog_code.util import session_util
from prog_code.util import file_util
from prog_code.util import mail_util
from prog_code.util import session_util

app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

app.config.from_pyfile('flask_config.cfg')
app.config['UPLOAD_FOLDER'] = file_util.UPLOAD_FOLDER
app.config['MAIL_PORT'] = 587
app.config['MAIL_FAIL_SILENTLY'] = False
mail_util.init_mail(app)

from prog_code.controller import access_data_controllers
from prog_code.controller import account_controllers
from prog_code.controller import api_key_controllers
from prog_code.controller import edit_user_controllers
from prog_code.controller import enter_data_controllers
from prog_code.controller import format_controllers

@app.route("/")
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
