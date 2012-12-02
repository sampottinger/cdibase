"""Logic for managing user accounts and user access controls.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import random
import string

import werkzeug

import flask.ext.mail as flask_mail

from ..struct import models

import db_util
import mail_util

SIGN_UP_MSG = '''Hello!

You can access DaxlabBase with the following credentials:

Email: %s
Password: %s

Please don't forget to change your password after logging in!

All the best,
Sam
DaxlabBase Application Curator
sam@gleap.org / daxlab@gleap.org
'''

RESET_PASSWORD_MSG = '''Hello!

You (or someone pretending to be you) reset your password on DaxlabBase. You can now log in with the following credentials:

Email: %s
Password: %s

Please don't forget to change your password after logging in! If you didn't request a change in password, please email daxlab@gleap.org.

All the best,
Sam
DaxlabBase Application Curator
sam@gleap.org / daxlab@gleap.org
'''


def generate_password(pass_len=10):
    chars = string.letters + string.digits
    return ''.join([random.choice(chars) for i in range(pass_len)])

def create_new_user(email, can_enter_data, can_access_data, can_change_formats,
    can_admin):
    email = email.lower()
    password = generate_password()
    pass_hash = werkzeug.security.generate_password_hash(password)
    user = models.User(email, pass_hash, can_enter_data, can_access_data,
        can_change_formats, can_admin)
    db_util.create_user_model(user)

    registration_message = flask_mail.Message(
        "Your DaxlabBase Account",
        sender="daxlab@gleap.org",
        recipients=[email],
        body=SIGN_UP_MSG % (email, password)
    )

    mail_util.send_msg(registration_message)

def check_user_password(email, password):
    email = email.lower()
    user = db_util.load_user_model(email)
    if not user:
        return False
    pass_hash = user.password_hash
    return werkzeug.security.check_password_hash(pass_hash, password)

def change_user_password(email, password):
    email = email.lower()
    user = db_util.load_user_model(email)
    user.password_hash = werkzeug.security.generate_password_hash(password)
    db_util.save_user_model(user)

def update_user_permissions(email, can_enter_data, can_access_data,
    can_change_formats, can_admin):
    email = email.lower()
    user = db_util.load_user_model(email)
    user.can_enter_data = can_enter_data
    user.can_access_data = can_access_data
    user.can_change_formats = can_change_formats
    user.can_admin = can_admin
    db_util.save_user_model(user)

def reset_password(email, pass_len=10):
    email = email.lower()
    new_pass = generate_password(pass_len)
    change_user_password(email, new_pass)

    registration_message = flask_mail.Message(
        "Your DaxlabBase Account",
        sender="daxlab@gleap.org",
        recipients=[email],
        body=RESET_PASSWORD_MSG % (email, new_pass)
    )

    mail_util.send_msg(registration_message)

def get_user(email):
    return db_util.load_user_model(email)

def delete_user(email):
    email = email.lower()
    db_util.delete_user_model(email)

def get_all_users():
    return db_util.get_all_user_models()
