import flask

import models

def require_login(orig_view):
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flask.session["error"] = "You are not currently logged in."
            return flask.redirect("/login")
        return orig_view(*args, **kwargs)
    decorated_function.__name__ = orig_view.__name__
    return decorated_function

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
    return flask.session["email"]

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
