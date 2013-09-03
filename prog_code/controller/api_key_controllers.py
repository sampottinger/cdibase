import json

import flask

from ..struct import models
from ..util import api_key_util
from ..util import db_util
from ..util import filter_util
from ..util import report_util
from ..util import session_util
from ..util import user_util

from daxlabbase import app

SPECIAL_API_QUERY_FIELDS = {
    'min_percentile': {'field': 'percentile', 'op': 'gteq'},
    'max_percentile': {'field': 'percentile', 'op': 'lteq'},
    'min_birthday': {'field': 'birthday', 'op': 'gteq'},
    'max_birthday': {'field': 'birthday', 'op': 'lteq'},
    'min_session_date': {'field': 'session_date', 'op': 'gteq'},
    'max_session_date': {'field': 'session_date', 'op': 'lteq'}
}

FLOAT_FIELDS = [
    'min_percentile',
    'max_percentile'
]

INTEGER_FIELDS = [
    'child_id',
    'gender',
    'session_num',
    'total_num_sessions',
    'words_spoken',
    'items_excluded',
    'extra_categories',
    'revision',
    'num_languages',
    'hard_of_hearing'
]

INGORE_FIELDS = [
    'format',
    'api_key'
]


def generate_error(msg, code):
    return json.dumps({"error": msg}), code


def make_filter(field, value):
    if field in FLOAT_FIELDS:
        value = float(value)
    elif field in INTEGER_FIELDS:
        value = int(value)

    filter_const_info = None
    if field in SPECIAL_API_QUERY_FIELDS:
        filter_const_info = SPECIAL_API_QUERY_FIELDS[field]
    else:
        filter_const_info = {'field': field, 'op': 'eq'}

    return models.Filter(
        filter_const_info['field'],
        filter_const_info['op'],
        value
    )


@app.route("/base/config_api_key")
@session_util.require_login(use_api_key=True)
def config_api_keys():
    """GUI page for configuring API keys.

    @return: Current API key and controls to modify that key.
    @rtype: flask.Response
    """
    user_id = session_util.get_user_id()
    return flask.render_template(
        "edit_api_keys.html",
        cur_page="conifg_api_key",
        api_key=api_key_util.get_api_key(user_id),
        **session_util.get_standard_template_values()
    )


@app.route("/base/config_api_key/new")
@session_util.require_login(use_api_key=True)
def create_api_key():
    user_id = session_util.get_user_id()
    api_key_util.create_new_api_key(user_id)
    flask.session["confirmation"] = "New API key generated."
    return flask.redirect("/base/config_api_key")


@app.route("/base/api/v0/mcdi_metadata.json")
def get_child_info_by_api():
    api_key = flask.request.args.get('api_key', None)
    if not api_key:
        return generate_error('No API key provided.', 400)

    api_key_record = db_util.get_api_key(api_key)
    if not api_key_record:
        return generate_error('Invalid API key provided.', 400)

    user = user_util.get_user(api_key_record.user_id)
    if not user:
        return generate_error('Invalid API key provided.', 400)

    if not user.can_use_api_key:
        return generate_error('User not authorized to use API keys.', 403)

    if not user.can_access_data:
        return generate_error('User not authorized to use access database.',
            403)

    fields = filter(lambda (name, value): name not in INGORE_FIELDS,
        flask.request.args.items())
    db_filters = map(lambda x: make_filter(*x), fields)

    present_format = flask.request.args.get('format', None)
    if present_format:
        present_format = db_util.load_presentation_model(present_format)
    
    matching_snapshots = filter_util.run_search_query(db_filters, "snapshots")
    serialized_snapshots_by_child_id = {}

    for snapshot in matching_snapshots:
        child_id = snapshot.child_id
        
        if not child_id in serialized_snapshots_by_child_id:
            serialized_snapshots_by_child_id[child_id] = []
        
        snapshot_serialized = report_util.serialize_snapshot(
            snapshot,
            presentation_format=present_format,
            report_dict=True,
            include_words=False
        )
        
        serialized_snapshots_by_child_id[child_id].append(snapshot_serialized)

    return json.dumps(serialized_snapshots_by_child_id)
