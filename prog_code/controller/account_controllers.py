"""Logic for letting a user manage their own account / authentication status.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import flask

from ..util import session_util
from ..util import user_util

from daxlabbase import app


@app.route("/account/login", methods=["GET", "POST"])
def login():
    """Controller to let a user authenticate with the application.

    @return: HTML form on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == "GET":
        return flask.render_template(
            "login.html",
            cur_page="login",
            **session_util.get_standard_template_values()
        )

    elif request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if not user_util.check_user_password(email, password):
            flask.session["error"] = "Whoops! Either your username or password was wrong."
            return flask.redirect("/account/login")

        flask.session["email"] = email
        flask.session["confirmation"] = "Hello %s! You logged in successfully." % email
        return flask.redirect("/")


@app.route("/account/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Controller to let a user reset their password if they forgot it.

    @return: HTML form to request new password on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == "GET":
        return flask.render_template(
            "forgot_password.html",
            cur_page="forgot_password",
            **session_util.get_standard_template_values()
        )

    elif request.method == "POST":
        email = request.form.get("email", "")
        user_util.reset_password(email)
        flask.session["confirmation"] = "A new password has been sent to %s." % email
        return flask.redirect("/account/login")


@app.route("/account/logout")
def logout():
    """Controller to end a user's session with the application.

    @return: Redirect
    @rtype: flask.Response
    """
    session_util.logout()
    flask.session["confirmation"] = "Logged out."
    return flask.redirect("/")


@app.route("/account")
@session_util.require_login()
def account():
    """Controller to render index page of controlls for editing a user account.

    @return: HTML listing of controls
    @rtype: flask.Response
    """
    return flask.render_template(
        "account.html",
        cur_page="account",
        **session_util.get_standard_template_values()
    )


@app.route("/account/change_password", methods=["GET", "POST"])
@session_util.require_login()
def change_password():
    """Controller to change a user password.

    @return: HTML form on GET and redirect on POST
    @rtype: flask.Response
    """
    request = flask.request
    if request.method == "GET":
        return flask.render_template(
            "change_password.html",
            cur_page="account",
            **session_util.get_standard_template_values()
        )

    elif request.method == "POST":
        email = session_util.get_user_email()
        cur_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_new_password = request.form.get("confirm_new_password", "")

        if not user_util.check_user_password(email, cur_password):
            flask.session["error"] = "Current password incorrect."
            return flask.redirect("/account/change_password")

        if not new_password == confirm_new_password:
            flask.session["error"] = "New password and confirmation of new password are not the same."
            return flask.redirect("/account/change_password")

        user_util.change_user_password(email, new_password)
        flask.session["confirmation"] = "Your password has been updated."
        return flask.redirect("/account")
