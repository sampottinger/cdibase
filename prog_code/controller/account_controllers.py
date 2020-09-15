"""Logic for letting a user manage their own account / authentication status.

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

import flask

from ..util import constants
from ..util import session_util
from ..util import user_util

from cdibase import app

WRONG_CREDENTIALS_MSG = 'Whoops! Either your username or password was wrong.'
CONFIRM_PASSWORD_MISMATCH_MSG = 'New password and confirmation of new ' \
    'password are not the same.'
CURRENT_PASSWORD_INCORRECT_MSG = 'Current password incorrect.'
SUCCESS_LOGIN_MSG = 'Hello %s! You logged in successfully.'
PASSWORD_RESET_MSG = 'A new password has been sent to %s.'
LOGGED_OUT_MSG = 'Logged out.'
UPDATED_PASSWORD_MSG = 'Your password has been updated.'

ERROR_ATTR = constants.ERROR_ATTR
CONFIRMATION_ATTR = constants.CONFIRMATION_ATTR
EMAIL_ATTR = 'email'
PASSWORD_ATTR = 'password'

LOGIN_URL = '/base/account/login'
HOME_URL = '/base'
CHANGE_PASSWORD_URL = '/base/account/change_password'
ACCOUNT_MANAGEMENT_URL = '/base/account'


@app.route('/base/account/login', methods=['GET', 'POST'])
def login():
    """Controller to let a user authenticate with the application.

    Controller that allows a user to log into the application. Note that this
    controller should not produce error messages that reveal the existance of
    accounts (report credentials incorrect not that an account does not exist).

    @return: HTML form on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == 'GET':
        return flask.render_template(
            'login.html',
            cur_page='login',
            **session_util.get_standard_template_values()
        )

    elif request.method == 'POST':
        email = request.form.get(EMAIL_ATTR, '')
        password = request.form.get(PASSWORD_ATTR, '')

        if not user_util.check_user_password(email, password):
            flask.session[ERROR_ATTR] = WRONG_CREDENTIALS_MSG
            return flask.redirect(LOGIN_URL)

        flask.session[EMAIL_ATTR] = email
        flask.session[CONFIRMATION_ATTR] = SUCCESS_LOGIN_MSG % email
        return flask.redirect(HOME_URL)


@app.route('/base/account/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Controller to let a user reset their password if they forgot it.

    Controller that allows users to reset their passwords. Note that this
    controller does not yield error messages that reveal the existance of an
    account.

    @return: HTML form to request new password on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == 'GET':
        return flask.render_template(
            'forgot_password.html',
            cur_page='forgot_password',
            **session_util.get_standard_template_values()
        )

    elif request.method == 'POST':
        email = request.form.get(EMAIL_ATTR, None)

        if email != None and user_util.get_user(email):
            user_util.reset_password(email)

        flask.session[CONFIRMATION_ATTR] = PASSWORD_RESET_MSG % email
        return flask.redirect(LOGIN_URL)


@app.route('/base/account/logout')
def logout():
    """Controller to end a user's session with the application.

    @return: Redirect
    @rtype: flask.Response
    """
    session_util.logout()
    flask.session[CONFIRMATION_ATTR] = LOGGED_OUT_MSG
    return flask.redirect(HOME_URL)


@app.route('/base/account')
@session_util.require_login()
def account():
    """Controller to render index page of controlls for editing a user account.

    @return: HTML listing of controls
    @rtype: flask.Response
    """
    return flask.render_template(
        'account.html',
        cur_page='account',
        **session_util.get_standard_template_values()
    )


@app.route('/base/account/change_password', methods=['GET', 'POST'])
@session_util.require_login()
def change_password():
    """Controller to change a user password.

    Controller that allows a user to change his / her password. Will reject
    POST if the current password entered is incorrect, the confirmation password
    doesn't match the new password, or if the either the current password,
    new password, or confirmation of new password is empty. A session error
    or confirmation message will be also set and the user will be redirected to
    the appropriate URL if POST.

    @return: HTML form on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == 'GET':
        return flask.render_template(
            'change_password.html',
            cur_page='account',
            **session_util.get_standard_template_values()
        )

    elif request.method == 'POST':
        email = session_util.get_user_email()
        cur_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_new_password = request.form.get('confirm_new_password', '')

        if '' in [cur_password, new_password, confirm_new_password]:
            flask.session[ERROR_ATTR] = CURRENT_PASSWORD_INCORRECT_MSG
            return flask.redirect(CHANGE_PASSWORD_URL)

        if not user_util.check_user_password(email, cur_password):
            flask.session[ERROR_ATTR] = CURRENT_PASSWORD_INCORRECT_MSG
            return flask.redirect(CHANGE_PASSWORD_URL)

        if not new_password == confirm_new_password:
            flask.session[ERROR_ATTR] = CONFIRM_PASSWORD_MISMATCH_MSG
            return flask.redirect(CHANGE_PASSWORD_URL)

        user_util.change_user_password(email, new_password)
        flask.session[CONFIRMATION_ATTR] = UPDATED_PASSWORD_MSG
        return flask.redirect(ACCOUNT_MANAGEMENT_URL)
