"""Logic for managing application users.

Logic for managing user and user access controlls for the application.

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

from daxlabbase import app

USER_NOT_FOUND_MSG = 'User \"%s\" could not be found.'
USER_ALREADY_EXISTS_MSG = 'User \"%s\" already exists. User not updated.'
ACCOUNT_UPDATED_MSG = 'Account updated for %s.'
EDIT_USERS_URL = '/base/edit_users'
EMAIL_NOT_PROVIDED_MSG = 'Email not provided. Please try again.'
ACCOUNT_CREATED_MSG = 'Account created for %s.'
ADD_USERS_URL = '/base/edit_users/_add'

@app.route('/base/edit_users')
@session_util.require_login(admin=True)
def edit_users():
    """Edit users with access to the application.

    @return: List of users with access to the application with links to add to,
        edit, and delete those accounts.
    @rtype: flask.Response
    """
    return flask.render_template(
        'edit_users.html',
        cur_page='edit_users',
        users=user_util.get_all_users(),
        **session_util.get_standard_template_values()
    )


@app.route('/base/edit_users/<email>/delete')
@session_util.require_login(admin=True)
def delete_user(email):
    """Controller to remove a user's access to this application.

    Controller that removes a record of a user account and ends that user's
    access to the application.

    @param email: The email of the user account to delete.
    @type email: str
    @return: Redirect
    @rtype: flask.Response
    """
    if not user_util.get_user(email):
        flask.session[constants.ERROR_ATTR] = USER_NOT_FOUND_MSG % email
        return flask.redirect(EDIT_USERS_URL)

    user_util.delete_user(email)
    flask.session[constants.CONFIRMATION_ATTR] = ACCOUNT_UPDATED_MSG % email
    return flask.redirect(EDIT_USERS_URL)


@app.route('/base/edit_users/<email>/edit', methods=['GET', 'POST'])
@session_util.require_login(admin=True)
def edit_user(email):
    """Controller to edit a user's account in this application.

    @param email: The email of the user account to edit.
    @type email: str
    @return: Redirect
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == 'GET':
        return flask.render_template(
            'edit_user.html',
            cur_page='edit_users',
            target_user=user_util.get_user(email),
            action_label='Edit User Account',
            **session_util.get_standard_template_values()
        )
    
    else:
        new_email = request.form.get('new_email', '')

        if not user_util.get_user(email):
            msg = USER_NOT_FOUND_MSG % email
            flask.session[constants.ERROR_ATTR] = msg
            return flask.redirect(request.path)

        if new_email != email and user_util.get_user(new_email):
            msg = USER_ALREADY_EXISTS_MSG % new_email
            flask.session[constants.ERROR_ATTR] = msg
            return flask.redirect(request.path)

        on_val = constants.FORM_SELECTED_VALUE
        user_util.update_user(
            email,
            new_email,
            request.form.get('can_enter_data', '') == on_val,
            request.form.get('can_delete_data', '') == on_val,
            request.form.get('can_import_data', '') == on_val,
            request.form.get('can_edit_parents', '') == on_val,
            request.form.get('can_access_data', '') == on_val,
            request.form.get('can_change_formats', '') == on_val,
            request.form.get('can_use_api_key', '') == on_val,
            request.form.get('can_admin', '') == on_val
        )
        flask.session[constants.CONFIRMATION_ATTR] = ACCOUNT_UPDATED_MSG % email
        return flask.redirect(EDIT_USERS_URL)


@app.route('/base/edit_users/_add', methods=['GET', 'POST'])
@session_util.require_login(admin=True)
def add_user():
    """Controller to add a new user account to this application.

    @return: HTML form on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == 'GET':
        return flask.render_template(
            'edit_user.html',
            cur_page='edit_users',
            action_label='Create User',
            **session_util.get_standard_template_values()
        )

    elif request.method == 'POST':
        email = request.form.get('new_email', '')

        if email == '':
            flask.session[constants.ERROR_ATTR] = EMAIL_NOT_PROVIDED_MSG
            return flask.redirect(ADD_USERS_URL)

        if user_util.get_user(email):
            msg = USER_ALREADY_EXISTS_MSG % email
            flask.session[constants.ERROR_ATTR] = msg
            return flask.redirect(ADD_USERS_URL)

        on_val = constants.FORM_SELECTED_VALUE

        user_util.create_new_user(
            email,
            request.form.get('can_enter_data', '') == on_val,
            request.form.get('can_delete_data', '') == on_val,
            request.form.get('can_import_data', '') == on_val,
            request.form.get('can_edit_parents', '') == on_val,
            request.form.get('can_access_data', '') == on_val,
            request.form.get('can_change_formats', '') == on_val,
            request.form.get('can_use_api_key', '') == on_val,
            request.form.get('can_admin', '') == on_val
        )
        flask.session[constants.CONFIRMATION_ATTR] = ACCOUNT_CREATED_MSG % email
        return flask.redirect(EDIT_USERS_URL)
