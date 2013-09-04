"""Logic for managing parent accounts.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import flask

from ..util import db_util
from ..util import parent_account_util
from ..util import session_util
from ..util import user_util

from ..struct import models

from daxlabbase import app


@app.route("/base/parent_accounts", methods=["GET", "POST"])
@session_util.require_login(edit_parents=True)
def edit_parent_accounts():
    request = flask.request
    if request.method == "POST":
        form_id = parent_account_util.generate_unique_mcdi_form_id()
        global_id = request.form.get("global_id", "")
        study_id = request.form.get("study_id", "")
        study = request.form.get("study", "")
        gender = request.form.get("gender", "")
        age = request.form.get("age", "")
        birthday = request.form.get("birthday", "")
        session_date = request.form.get("session_date", "")
        session_num = request.form.get("session_num", "")
        items_excluded = request.form.get("items_excluded", "")
        extra_categories = request.form.get("extra_categories", "")
        languages = request.form.get("languages", "")
        languages = languages.split(",")
        hard_of_hearing = request.form.get("hard_of_hearing", "off") == "on"
        child_name = request.form.get("child_name", "")
        parent_email = request.form.get("parent_email", "")
        mcdi_type = request.form.get("mcdi_type", "")

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
            age,
            birthday,
            session_date,
            session_num,
            items_excluded,
            extra_categories,
            0,
            ",".join(languages),
            len(languages),
            hard_of_hearing
        )

        resolver = parent_account_util.AttributeResolutionResolver()
        resolver.fill_parent_form_defaults(new_form)

        db_util.insert_parent_form(new_form)
        parent_account_util.send_mcdi_email(new_form)

        flask.session["confirmation"] = "MCDI form sent."

        return flask.redirect('/base/parent_accounts')

    else:
        return flask.render_template(
            "parent_accounts.html",
            cur_page="edit_parents",
            users=user_util.get_all_users(),
            mcdi_formats=db_util.load_mcdi_model_listing(),
            **session_util.get_standard_template_values()
        )