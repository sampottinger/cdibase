import flask

import models

def get_error():
    error = flask.session.get("error", None)
    flask.session["error"] = None
    return error

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
