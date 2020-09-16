"""Logic for managing user accounts and user access controls.

Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

@author: Sam Pottinger
@license: GNU GPL v3
"""
import random
import string
import typing

import werkzeug

from ..struct import models

import prog_code.util.db_util as db_util
import prog_code.util.mail_util as mail_util

SIGN_UP_MSG = '''Hello!

You can access CdiBase with the following credentials:

Email: %s
Password: %s

Please don't forget to change your password after logging in!

All the best,
CdiBase
'''

RESET_PASSWORD_MSG = '''Hello!

You (or someone pretending to be you) reset your password on CdiBase. You can now log in with the following credentials:

Email: %s
Password: %s

Please don't forget to change your password after logging in! If you didn't request a change in password, please email cdi@gleap.org.

All the best,
CdiBase
'''


def force_get_user(email: str) -> models.User:
    """Get a user record by email and assert the user exists.

    @param email: The email address of the user.
    @returns: User account record.
    """
    user = db_util.load_user_model(email)
    assert user != None
    return user # type: ignore


def generate_password(pass_len: int = 10) -> str:
    """Generate a random user password.

    @keyword pass_len: The length in characters of the password to generate.
    @type pass_len: int
    """
    chars = string.ascii_letters + string.digits
    return ''.join([random.choice(chars) for i in range(pass_len)])


def create_new_user(email: str, can_enter_data: bool, can_delete_data: bool, can_import_data: bool,
    can_edit_parents: bool, can_access_data: bool, can_change_formats: bool, can_use_api_key: bool,
    can_admin: bool) -> None:
    """Create and persist a new user, sending account info by email in process.

    @param email: The email address of the user to create an account for.
    @type email: str
    @param can_enter_data: Indicates if the user can add new data to the lab
        dataset.
    @type can_enter_data: bool
    @param can_delete_data: Indicates if the user can delete data from the lab
        dataset.
    @type can_delete_data: bool
    @param can_enter_data: Indicates if the user can add new data to the lab
        dataset by importing a CSV file.
    @type can_enter_data: bool
    @param can_access_data: Indicates if the user can access existing lab data.
    @type can_access_data: bool
    @param can_change_formats: Indicates if the user can edit CDI forms,
        presentation formats, and percentile data tables.
    @type can_change_formats: bool
    @param can_use_api_key: Indicates if this user can use an API key.
    @type can_use_api_key: bool
    @param can_admin: Indicates if the user can administer user accounts and
        user access control.
    @type can_admin: bool
    """
    email = email.lower()
    password = generate_password()
    pass_hash = werkzeug.generate_password_hash(password,
        method='sha512')
    user = models.User(
        -1,
        email,
        pass_hash,
        can_enter_data,
        can_delete_data,
        can_import_data,
        can_edit_parents,
        can_access_data,
        can_change_formats,
        can_use_api_key,
        can_admin
    )
    db_util.create_user_model(user)

    mail_util.send_msg(
        email,
        'Your CdiBase Account',
        SIGN_UP_MSG % (email, password)
    )

def check_user_password(email: str, password: str) -> bool:
    """Check if the given password is correct.

    @param email: The email of the user to check a password for.
    @type email: str
    @param password: The password to check.
    @type password: str
    @return: True if the password is correct and False otherwise.
    @rtype: bool
    """
    email = email.lower()
    user = force_get_user(email)
    if not user:
        return False
    pass_hash = str(user.password_hash)
    try:
        return werkzeug.check_password_hash(pass_hash, password)
    except:
        return False

def change_user_password(email: str, password: str) -> None:
    """Change a user's account password.

    @param email: The email of the user to change account passwords for.
    @type email: str
    @param password: The new password to use for the account.
    @type password: str
    """
    email = email.lower()
    user = force_get_user(email)
    pass_hash = werkzeug.generate_password_hash(password,
        method='sha512')
    user.password_hash = pass_hash
    db_util.save_user_model(user)

def update_user(orig_email: str, email: str, can_enter_data: bool, can_delete_data: bool,
    can_import_data: bool, can_edit_parents: bool, can_access_data: bool, can_change_formats: bool,
    can_use_api_key: bool, can_admin: bool) -> None:
    """Change a user's account.

    @param orig_email: The email of the user whose account permissions is being
        changed.
    @type orig_email: str
    @param new_email: The new email address to give to this user.
    @type new_email: str
    @param can_enter_data: Indicate if the user can enter new data into the lab
        database.
    @type can_enter_data: bool
    @param can_delete_data: Indicate if the user can delete data from the lab
        database.
    @type can_delete_data: bool
    @param can_import_data: Indicate if the user can import data from the lab
        database.
    @type can_import_data: bool
    @param can_access_data: Indicate if the user can access existing lab data.
    @type can_access_data: bool
    @param can_change_formats: Indicate if the user can change CDI forms, CSV
        presentation formats, and percentile tables.
    @type can_change_formats: bool
    @param can_use_api_key: Indicates if this user can use an API key.
    @type can_use_api_key: bool
    @param can_admin: Indicates if this user can edit other users' accounts and
        permissions.
    @type can_admin: bool
    """
    email = email.lower()
    user = force_get_user(orig_email)
    user.email = email
    user.can_enter_data = can_enter_data
    user.can_delete_data = can_delete_data
    user.can_import_data = can_import_data
    user.can_edit_parents = can_edit_parents
    user.can_access_data = can_access_data
    user.can_change_formats = can_change_formats
    user.can_use_api_key = can_use_api_key
    user.can_admin = can_admin
    db_util.save_user_model(user, existing_email=orig_email)

def reset_password(email: str, pass_len: int = 10) -> None:
    """Set user's password to random string and send email with new credentials.

    @param email: The email of the user whose account password needs to be
        reset.
    @type email: str
    @keyword pass_len: The length in characters of the new password to generate.
    @type pass_len: int
    """
    email = email.lower()
    new_pass = generate_password(pass_len)
    change_user_password(email, new_pass)

    mail_util.send_msg(
        email,
        'Your CdiBase Account',
        RESET_PASSWORD_MSG % (email, new_pass)
    )

def get_user(identifier: str) -> typing.Optional[models.User]:
    """Get user account information for the user with the given email.

    @param identifier: The email address of the user to get account information
        for. May also be integer ID.
    @type identifier: str or int
    @return: User account info for use with given email address.
    @rtype: models.User
    """
    return db_util.load_user_model(str(identifier))

def delete_user(email: str) -> None:
    """Delete the user with the given email address.

    @param email: The email address of the user whose account should be deleted.
    @type email: str
    """
    email = email.lower()
    db_util.delete_user_model(email)

def get_all_users() -> typing.List[models.User]:
    """Get a listing of all of the users registered with the application.

    @return: Collection of all user accounts for this application.
    @rtype: Collection of models.User
    """
    return db_util.get_all_user_models()
