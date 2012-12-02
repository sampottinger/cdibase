import flask

from ..struct import models

import user_util

def get_standard_template_values():
    return {
        "email": get_user_email(),
        "confirmation": get_confirmation(),
        "error": get_error()
    }

def require_login(access_data=False, admin=False, enter_data=False,
    change_formats=False):
    def wrap(orig_view):
        def decorated_function(*args, **kwargs):
            if not is_logged_in():
                flask.session["error"] = "You are not currently logged in."
                return flask.redirect("/login")
            user = user_util.get_user(get_user_email())
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
            return orig_view(*args, **kwargs)
        decorated_function.__name__ = orig_view.__name__
        return decorated_function
    return wrap

def logout():
    if "email" in flask.session:
        del flask.session["email"]

def is_logged_in():
    return "email" in flask.session

def get_error():
    error = flask.session.get("error", None)
    flask.session["error"] = None
    return error

def get_user_email():
    return flask.session.get("email", None)

def get_confirmation():
    msg = flask.session.get("confirmation", None)
    flask.session["confirmation"] = None
    return msg

def get_filters():
    filters = flask.session.get("filters", None)
    if not filters:
        return []
    return filters

def add_filter(new_filter):
    filters = flask.session.get("filters", None)
    if not filters:
        filters = []
    filters.append(new_filter)
    flask.session["filters"] = filters

def delete_filter(index):
    filters = flask.session.get("filters", None)
    if not filters:
        return False
    if index >= len(filters):
        return False
    del filters[index]
    return True
