"""Logic for managing parent accounts.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import flask

from ..util import session_util
from ..util import user_util

from daxlabbase import app


@app.route("/base/parent_accounts")
@session_util.require_login(edit_parents=True)
def start():
    return flask.render_template(
        "parent_accounts.html",
        cur_page="edit_parents",
        users=user_util.get_all_users(),
        **session_util.get_standard_template_values()
    )