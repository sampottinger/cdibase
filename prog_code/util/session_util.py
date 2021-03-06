"""Logic for managing user sessions and their contents.

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
import typing

import flask

from ..struct import models

import prog_code.util.constants as constants
import prog_code.util.user_util as user_util
import prog_code.util.db_util as db_util

LOGIN_AGAIN_MSG = 'Whoops! For security, please log in again.'
NOT_AUTHORIZED_ACCESS_DATA_MSG = 'You are not authorized to access data.'
NOT_AUTHORIZED_PARENTS_MSG = 'You are not authorized to edit parent accounts.'
NOT_AUTHORIZED_ADMIN_MSG = 'You are not authorized to admin.'
NOT_AUTHORIZED_ENTER_DATA_MSG = 'You are not authorized to enter data.'
NOT_AUTHORIZED_DELETE_DATA_MSG = 'You are not authorized to delete data.'
NOT_AUTHORIZED_IMPORT_DATA_MSG = 'You are not authorized to import data.'
NOT_AUTHORIZED_CHANGE_FORMATS_MSG = 'You are not authorized to change formats.'
NOT_AUTHORIZED_API_KEYS_MSG = 'You are not authorized to use API keys.'


def get_user_if_provided(email: typing.Optional[str]) -> typing.Optional[models.User]:
    """Get a user by the given email address.

    @param email: The email address to look up.
    @returns: None if email does not belong to any user or is None. User otherwise.
    """
    if email == None:
        return None
    email_realized: str = email # type: ignore
    return user_util.get_user(email_realized)


def get_standard_template_values() -> typing.Dict[str, typing.Any]:
    """Get session information necessary to render any application page.

    Get session information necessary to render any application page including
    the email of the user currently logged in (or None if visitor not logged
    in), any waiting confirmation messages, and any waiting error messages.

    @return: Dictionary of values for rendering HTML templates.
    @rtype: dict
    """
    return {
        'email': get_user_email(),
        'confirmation': get_confirmation(),
        'error': get_error(),
        'user': get_user_if_provided(get_user_email()),
        'scroll': get_scroll()
    }


def create_args_snapshot() -> typing.Dict[str, typing.Any]:
    """Create a snapshot of arguments from a flask request.

    @returns: Description of items provided.
    """
    return flask.request.form.items() + flask.request.args.items()


def require_login(access_data: bool = False, admin: bool = False, enter_data: bool = False,
        delete_data: bool = False, import_data: bool = False, edit_parents: bool = False,
        change_formats: bool = False, use_api_key: bool = False) -> typing.Callable[[typing.Callable], typing.Callable]:
    """Decorator that requires that a user be logged in to do an operation.

    Decorator that requires that a user be logged in to do an operation and
    automatically redirect if visitor is not logged in or if visitor has
    insufficient permissions.

    @keyword access_data: If True, require that the user have permission to
        access existing database entries. Defaults to False.
    @type access_data: bool
    @keyword admin: If True, require that the user have permission to administer
        other user accounts and user access control. Defaults to False.
    @type admin: bool
    @keyword enter_data: If True, require that the user have permission to
        access enter new data into the database. Defaults to False.
    @type enter_data: bool
    @keyword change_formats: If True, require that the user have permission to
        access / edit CDI forms, CSV presentation formats, and percentile
        tables. Defaults to False.
    @type access_data: bool
    @keyword use_api_key: If True, require that the user has permission to use
        API keys. Defaults to False.
    @type: use_api_key: bool
    """
    def wrap(orig_view):
        def decorated_function(*args, **kwargs):
            if not is_logged_in():
                flask.session[constants.ERROR_ATTR] = LOGIN_AGAIN_MSG
                return flask.redirect("/base/account/login")
            user = get_user_if_provided(get_user_email())
            if not user:
                del flask.session["email"]
                flask.session[constants.ERROR_ATTR] = LOGIN_AGAIN_MSG
                return flask.redirect("/base/account/login")
            if access_data and not user.can_access_data:
                msg = NOT_AUTHORIZED_ACCESS_DATA_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect("/base")
            if edit_parents and not user.can_edit_parents:
                flask.session[constants.ERROR_ATTR] = NOT_AUTHORIZED_PARENTS_MSG
                return flask.redirect("/base")
            if admin and not user.can_admin:
                flask.session[constants.ERROR_ATTR] = NOT_AUTHORIZED_ADMIN_MSG
                return flask.redirect("/base")
            if enter_data and not user.can_enter_data:
                msg = NOT_AUTHORIZED_ENTER_DATA_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect("/base")
            if delete_data and not user.can_delete_data:
                msg = NOT_AUTHORIZED_DELETE_DATA_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect("/base")
            if import_data and not user.can_import_data:
                msg = NOT_AUTHORIZED_IMPORT_DATA_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect("/base")
            if change_formats and not user.can_change_formats:
                msg = NOT_AUTHORIZED_CHANGE_FORMATS_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect("/base")
            if use_api_key and not user.can_use_api_key:
                msg = NOT_AUTHORIZED_API_KEYS_MSG
                flask.session[constants.ERROR_ATTR] = msg
                return flask.redirect("/base")
            return orig_view(*args, **kwargs)
        decorated_function.__name__ = orig_view.__name__
        return decorated_function
    return wrap


def logout() -> None:
    """Remove user information from current visitor session."""
    if 'email' in flask.session:
        del flask.session['email']


def is_logged_in() -> bool:
    """Determine if current user is authenticated as an application user.

    @return: True if the current user is currently authenticated and False
        otherwise.
    @rtype: bool
    """
    return 'email' in flask.session


def get_error() -> typing.Optional[str]:
    """Get any waiting errors for the current user.

    Get any errors waiting for the current user and delete that message as it is
    returned.

    @return: None if no error waiting or error description if there is a pending
        message for the user.
    @rtype: str
    """
    error = flask.session.get(constants.ERROR_ATTR, None)
    flask.session[constants.ERROR_ATTR] = None
    return error


def get_user_email() -> typing.Optional[str]:
    """Get the email of the currently logged in user.

    @return: The email of the user currently logged in who is making the current
        request or None if the current user is not currently authenticated.
    @rtype: str
    """
    return flask.session.get('email', None)


def get_user_email_force() -> str:
    """Get the email of the currently logged in user.

    @return: The email of the user currently logged in who is making the current
        request. Throw error if it is not available.
    @rtype: str
    """
    user_email = get_user_email()
    assert user_email != None
    return user_email # type: ignore


def get_user_id() -> typing.Optional[int]:
    """Get the id of the user currently logged in.

    @returns: Current user ID or None if no session.
    """
    user = get_user_if_provided(get_user_email())
    if not user:
        return None
    return user.db_id


def get_user_id_force() -> int:
    """Get the id of the user currently logged in and assert not None

    @returns: Current user ID.
    """
    result = get_user_id()
    assert result != None
    return result # type: ignore


def get_confirmation() -> typing.Optional[str]:
    """Get any waiting confirmation messages for the current user.

    Get any confirmation messages waiting for the current user and delete that
    message as it is returned.

    @return: None if no message waiting or error description if there is a
        pending message for the user.
    @rtype: str
    """
    msg = flask.session.get(constants.CONFIRMATION_ATTR, None)
    flask.session[constants.CONFIRMATION_ATTR] = None
    return msg


def get_scroll():
    """Get any waiting confirmation messages for the current user.

    Get any confirmation messages waiting for the current user and delete that
    message as it is returned.

    @return: None if no message waiting or error description if there is a
        pending message for the user.
    @rtype: str
    """
    scroll = flask.session.get('scroll', False)
    flask.session['scroll'] = False
    return scroll


def serialize_filter(target_filter):
    """Turn a filter model into a dictionary serialization.

    @param target_filter: The filter to serialize.
    @type target_filter: models.Filter
    @return: Dictionary serailzation of the provided filter.
    @rtype: dict
    """
    return {
        'field': target_filter.field,
        'operator': target_filter.operator,
        'operand': target_filter.operand,
        'operand_float': target_filter.operand_float
    }


def unserialize_filter(target_filter_dict):
    """Turn a Filter model serialization into an actaul Filter model instance.

    @param target_filter_dict: The dictionary serailization to deserialize.
    @type target_filter_dict: dict
    @return: Filter model instance loaded from the provided serialization.
    @rtype: models.Filter
    """
    return models.Filter(
        target_filter_dict['field'],
        target_filter_dict['operator'],
        target_filter_dict['operand']
    )


def get_filters_serialized(session=None):
    if session == None:
        session = flask.session
    return session.get('filters', None)


def get_filters(session=None):
    """Get a collection of filters that the current user has created.

    Get all of the filters this current user has created as part of the query
    they are currently buildling.

    @return: Collection of filters in the query the user is currently building.
    @rtype: Collection of models.Filter
    """
    filters = get_filters_serialized(session)
    if not filters:
        return []
    return list(map(unserialize_filter, filters))


def add_filter(new_filter, sess=None):
    """Add a filter to the query the user is currently building.

    @param new_filter: The filter to add to the current user's current query.
    @type new_filter: models.Filter
    """
    if sess == None:
        sess = flask.session

    filters = get_filters(sess)
    if not filters:
        filters = []
    filters.append(new_filter)
    sess['filters'] = list(map(serialize_filter, filters))


def delete_filter(index):
    """Delete a filter from the query the user is currently building.

    @param index: The index / numerical ID of the query to delete from the
        collection of filters the user has in his / her current query (
        collection returned by get_filters)
    @type index: int
    """
    filters = flask.session.get('filters', None)
    if not filters:
        return False
    if index >= len(filters):
        return False
    del filters[index]
    return True


def set_waiting_on_delete(value, session=None):
    """Indicate that the current user's status waiting for a download.

    Indicate that the current user's status waiting for a download to be
    rendered.

    @param value: The value (from constants) to indicate for the user's status.
    @type value: int
    """
    if session == None:
        session = flask.session
    session['waiting_on_delete'] = value


def is_waiting_on_delete(session=None):
    """Determine if a user is waiting on a download.

    @return: True if the user is waiting on a download and False otherwise.
    @rtype: bool
    """
    if session == None:
        session = flask.session
    return session.get('waiting_on_delete', False)


def set_waiting_on_download(value, session=None):
    """Indicate that the current user's status waiting for a download.

    Indicate that the current user's status waiting for a download to be
    rendered.

    @param value: The value (from constants) to indicate for the user's status.
    @type value: int
    """
    if session == None:
        session = flask.session
    session['waiting_on_download'] = value


def is_waiting_on_download(session=None):
    """Determine if a user is waiting on a download.

    @return: True if the user is waiting on a download and False otherwise.
    @rtype: bool
    """
    if session == None:
        session = flask.session
    return session.get('waiting_on_download', False)
