import json

import dateutil.parser as dateutil_parser
import flask

from ..struct import models
from ..util import api_key_util
from ..util import constants
from ..util import db_util
from ..util import filter_util
from ..util import report_util
from ..util import interp_util
from ..util import parent_account_util
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


@app.route('/base/api/v0/send_parent_forms', methods=['GET', 'POST'])
def send_parent_forms():
    request = flask.request
    api_key = request.args.get('api_key', None)
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

    if not user.can_edit_parents:
        return generate_error('User not authorized to use access database.',
            403)

    global_id_str = request.args.get("database_id", "")
    study_id_str = request.form.get("study_id", "")
    study_str = request.args.get("study", "")
    gender_str = request.form.get("gender", "")
    birthday_str = request.args.get("birthday", "")
    items_excluded_str = request.args.get("items_excluded", "")
    extra_categories_str = request.args.get("extra_categories", "")
    languages_str = request.args.get("languages", "")
    hard_of_hearing_str = request.args.get("hard_of_hearing", "")
    child_name_str = request.args.get("child_name", "")
    parent_email_str = request.args.get("parent_email", "")
    mcdi_type_str = request.args.get("mcdi_type", "")

    interpretation_format_name = request.args.get("format", "standard")
    interpretation_format = db_util.load_presentation_model(
        interpretation_format_name)

    if global_id_str == "":
        global_id_vals = []
    else:
        global_id_vals = global_id_str.split(',')

    if study_id_str == "":
        study_id_vals = []
    else:
        study_id_vals = study_id_str.split(',')

    if study_str == "":
        study_vals = []
    else:
        study_vals = study_str.split(',')

    if gender_str == "":
        gender_vals = []
    else:
        gender_vals = gender_str.split(',')

    if birthday_str == "":
        birthday_vals = []
    else:
        birthday_vals = birthday_str.split(',')

    if items_excluded_str == "":
        items_excluded_vals = []
    else:
        items_excluded_vals = items_excluded_str.split(',')

    if extra_categories_str == "":
        extra_categories_vals = []
    else:
        extra_categories_vals = extra_categories_str.split(',')

    if languages_str == "":
        languages_vals = []
    else:
        languages_vals = languages_str.split(',')

    if hard_of_hearing_str == "":
        hard_of_hearing_vals = []
    else:
        hard_of_hearing_vals = hard_of_hearing_str.split(',')

    if child_name_str == "":
        child_name_vals = []
    else:
        child_name_vals = child_name_str.split(',')

    if parent_email_str == "":
        parent_email_vals = []
    else:
        parent_email_vals = parent_email_str.split(',')

    if mcdi_type_str == "":
        mcdi_type_vals = []
    else:
        mcdi_type_vals = mcdi_type_str.split(',')


    lengths = [
        len(global_id_vals),
        len(study_id_vals),
        len(study_vals),
        len(gender_vals),
        len(birthday_vals),
        len(items_excluded_vals),
        len(extra_categories_vals),
        len(languages_vals),
        len(hard_of_hearing_vals),
        len(child_name_vals),
        len(parent_email_vals),
        len(mcdi_type_vals)
    ]

    length_set = set(lengths)
    length_set.remove(0)
    if len(length_set) > 1:
        return json.dumps({'error': 'Mismatched CSV list lengths.'}), 400
    num_records = list(length_set)[0]

    for i in range(0, num_records):

        if len(global_id_vals) != 0:
            global_id = global_id_vals[i]
        else:
            global_id = ""

        if len(study_id_vals) != 0:
            study_id = study_id_vals[i]
        else:
            study_id = ""

        if len(study_vals) != 0:
            study = study_vals[i]
        else:
            study = ""

        if len(gender_vals) != 0:
            gender = gender_vals[i]
        else:
            gender = ""

        if len(birthday_vals) != 0:
            birthday = birthday_vals[i]
        else:
            birthday = ""

        if len(items_excluded_vals) != 0:
            items_excluded = items_excluded_vals[i]
        else:
            items_excluded = ""

        if len(extra_categories_vals) != 0:
            extra_categories = extra_categories_vals[i]
        else:
            extra_categories = ""

        if len(languages_vals) != 0:
            languages = languages_vals[i]
        else:
            languages = ""

        if len(hard_of_hearing_vals) != 0:
            hard_of_hearing = hard_of_hearing_vals[i]
        else:
            hard_of_hearing = ""

        if len(child_name_vals) != 0:
            child_name = child_name_vals[i]
        else:
            child_name = ""

        if len(parent_email_vals) != 0:
            parent_email = parent_email_vals[i]
        else:
            parent_email = ""

        if len(mcdi_type_vals) != 0:
            mcdi_type = mcdi_type_vals[i]
        else:
            mcdi_type = ""


        try:
            birthday = datetime.datetime.strptime(birthday, "%Y-%m-%dT%H:%M:%S")
            birthday = birthday.strftime('%Y/%m/%d')
        except:
            pass

        if parent_email == "":
            flask.session["error"] = "Parent email required."
            return flask.redirect('/base/parent_accounts')

        languages = languages.split('.')

        form_id = parent_account_util.generate_unique_mcdi_form_id()

        new_form = models.ParentForm(
            form_id,
            child_name,
            parent_email,
            mcdi_type,
            global_id,
            study_id,
            study,
            gender,
            birthday,
            items_excluded,
            extra_categories,
            ",".join(languages),
            len(languages),
            hard_of_hearing
        )

        resolver = parent_account_util.AttributeResolutionResolver()
        resolver.fill_parent_form_defaults(new_form)

        interpretation_vals = interpretation_format.details
        if new_form.gender == interpretation_vals['male']:
            new_form.gender = constants.MALE
        elif new_form.gender == interpretation_vals['female']:
            new_form.gender = constants.FEMALE
        elif new_form.gender == interpretation_vals['explicit_other']:
            new_form.gender = constants.OTHER_GENDER

        if new_form.hard_of_hearing == interpretation_vals['explicit_true']:
            new_form.hard_of_hearing = constants.EXPLICIT_TRUE
        elif new_form.hard_of_hearing == interpretation_vals['explicit_false']:
            new_form.hard_of_hearing = constants.EXPLICIT_FALSE

        db_util.insert_parent_form(new_form)
        parent_account_util.send_mcdi_email(new_form)

    return '{\'msg\': \'success\'}'


@app.route('/base/api/v0/send_parent_form', methods=['GET', 'POST'])
def send_parent_form():
    request = flask.request
    api_key = request.args.get('api_key', None)
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

    if not user.can_edit_parents:
        return generate_error('User not authorized to use access database.',
            403)

    interpretation_format_name = request.args.get("format", "standard")
    interpretation_format = db_util.load_presentation_model(
        interpretation_format_name)

    form_id = parent_account_util.generate_unique_mcdi_form_id()
    global_id = interp_util.safe_int_interpret(
        request.args.get("database_id", ""))
    study_id = request.form.get("study_id", "")
    study = request.args.get("study", "")
    gender = request.args.get("gender", "")
    birthday = request.args.get("birthday", "")
    items_excluded = interp_util.safe_int_interpret(
        request.args.get("items_excluded", ""))
    extra_categories = interp_util.safe_int_interpret(
        request.args.get("extra_categories", ""))
    languages = request.args.get("languages", "")
    languages = languages.split(".")
    hard_of_hearing = request.args.get("hard_of_hearing", "off") == "on"
    child_name = request.args.get("child_name", "")
    parent_email = request.args.get("parent_email", "")
    mcdi_type = request.args.get("mcdi_type", None)

    if mcdi_type == None or mcdi_type == "":
        return generate_error('Must specify mcdi_type.', 400)

    if db_util.load_mcdi_model(mcdi_type) == None:
        msg = '%s not a valid mcdi_type.' % mcdi_type
        return generate_error(msg, 400)

    if birthday != None and birthday != "":
        print birthday
        try:
            birthday = dateutil_parser.parse(birthday)
        except ValueError:
            return generate_error(
                'Must provide ISO8601 date for birthday.',
                400
            )
        birthday = birthday.strftime('%Y/%m/%d')


    if parent_email == "":
        flask.session["error"] = "Parent email required."
        return flask.redirect('/base/parent_accounts')

    new_form = models.ParentForm(
        form_id,
        child_name,
        parent_email,
        mcdi_type,
        global_id,
        study_id,
        study,
        gender,
        birthday,
        items_excluded,
        extra_categories,
        ",".join(languages),
        len(languages),
        hard_of_hearing
    )

    resolver = parent_account_util.AttributeResolutionResolver()
    resolver.fill_parent_form_defaults(new_form)

    interpretation_vals = interpretation_format.details
    if new_form.gender == interpretation_vals['male']:
        new_form.gender = constants.MALE
    elif new_form.gender == interpretation_vals['female']:
        new_form.gender = constants.FEMALE
    elif new_form.gender == interpretation_vals['explicit_other']:
        new_form.gender = constants.OTHER_GENDER

    if new_form.hard_of_hearing == interpretation_vals['explicit_true']:
        new_form.hard_of_hearing = constants.EXPLICIT_TRUE
    elif new_form.hard_of_hearing == interpretation_vals['explicit_false']:
        new_form.hard_of_hearing = constants.EXPLICIT_FALSE

    db_util.insert_parent_form(new_form)
    parent_account_util.send_mcdi_email(new_form)

    return '{\'msg\': \'success\'}'


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
