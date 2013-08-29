"""Logic for managing user sessions and their contents.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import flask

from ..struct import models

import user_util


def get_standard_template_values():
    """Get session information necessary to render any application page.

    Get session information necessary to render any application page including
    the email of the user currently logged in (or None if visitor not logged
    in), any waiting confirmation messages, and any waiting error messages.

    @return: Dictionary of values for rendering HTML templates.
    @rtype: dict
    """
    return {
        "email": get_user_email(),
        "confirmation": get_confirmation(),
        "error": get_error(),
        "user": user_util.get_user(get_user_email())
    }


def require_login(access_data=False, admin=False, enter_data=False,
    change_formats=False, use_api_key=False):
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
        access / edit MCDI forms, CSV presentation formats, and percentile
        tables. Defaults to False.
    @type access_data: bool
    @keyword use_api_key: If True, require that the user has permission to use
        API keys. Defaults to False.
    @tyep: use_api_key: bool
    """
    def wrap(orig_view):
        def decorated_function(*args, **kwargs):
            if not is_logged_in():
                flask.session["error"] = "Whoops! For security, please log in again."
                return flask.redirect("/account/login")
            user = user_util.get_user(get_user_email())
            if not user:
                del flask.session["email"]
                flask.session["error"] = "Whoops! For security, please log in again."
                return flask.redirect("/account/login")
            if access_data and not user.can_access_data:
                flask.session["error"] = "You are not authorized to access data."
                return flask.redirect("/")
            if admin and not user.can_admin:
                flask.session["error"] = "You are not authorized to admin."
                return flask.redirect("/")
            if enter_data and not user.can_enter_data:
                flask.session["error"] = "You are not authorized to enter data."
                return flask.redirect("/")
            if change_formats and not user.can_change_formats:
                flask.session["error"] = "You are not authorized to change formats."
                return flask.redirect("/")
            if use_api_key and not user.can_use_api_key:
                flask.session["error"] = "You are not authorized to use API keys."
                return flask.redirect("/")
            return orig_view(*args, **kwargs)
        decorated_function.__name__ = orig_view.__name__
        return decorated_function
    return wrap


def logout():
    """Remove user information from current visitor session."""
    if "email" in flask.session:
        del flask.session["email"]


def is_logged_in():
    """Determine if current user is authenticated as an application user.

    @return: True if the current user is currently authenticated and False
        otherwise.
    @rtype: bool
    """
    return "email" in flask.session


def get_error():
    """Get any waiting errors for the current user.

    Get any errors waiting for the current user and delete that message as it is
    returned.

    @return: None if no error waiting or error description if there is a pending
        message for the user.
    @rtype: str
    """
    error = flask.session.get("error", None)
    flask.session["error"] = None
    return error


def get_user_email():
    """Get the email of the currently logged in user.

    @return: The email of the user currently logged in who is making the current
        request or None if the current user is not currently authenticated.
    @rtype: str
    """
    return flask.session.get("email", None)


def get_user_id():
    """Get the id of the user currently logged in."""
    user = user_util.get_user(get_user_email())
    if not user:
        return None
    return user.db_id


def get_confirmation():
    """Get any waiting confirmation messages for the current user.

    Get any confirmation messages waiting for the current user and delete that
    message as it is returned.

    @return: None if no message waiting or error description if there is a
        pending message for the user.
    @rtype: str
    """
    msg = flask.session.get("confirmation", None)
    flask.session["confirmation"] = None
    return msg


def get_filters():
    """Get a collection of filters that the current user has created.

    Get all of the filters this current user has created as part of the query
    they are currently buildling.

    @return: Collection of filters in the query the user is currently building.
    @rtype: Collection of models.Filter
    """
    filters = flask.session.get("filters", None)
    if not filters:
        return []
    return filters


def add_filter(new_filter):
    """Add a filter to the query the user is currently building.

    @param new_filter: The filter to add to the current user's current query.
    @type new_filter: models.Filter
    """
    filters = flask.session.get("filters", None)
    if not filters:
        filters = []
    filters.append(new_filter)
    flask.session["filters"] = filters


def delete_filter(index):
    """Delete a filter from the query the user is currently building.

    @param index: The index / numerical ID of the query to delete from the
        collection of filters the user has in his / her current query (
        collection returned by get_filters)
    @type index: int
    """
    filters = flask.session.get("filters", None)
    if not filters:
        return False
    if index >= len(filters):
        return False
    del filters[index]
    return True
