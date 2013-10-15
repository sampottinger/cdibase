"""Logic for managing user API keys and other minuta.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import db_util
import user_util


def interp_csv_field(target):
    if target == '':
        return []
    else:
        return target.split(',')


def get_if_avail(target_list, index):
    if len(target_list) != 0:
        return target_list[index]
    else:
        return ''


def generate_new_api_key():
    found = False
    new_key = None

    while not found: 
        new_key = user_util.generate_password(pass_len=20).lower()
        found = db_util.get_api_key(new_key) == None

    return new_key


def get_api_key(user_id):
    return db_util.get_api_key(user_id)


def create_new_api_key(user_id):
    if get_api_key(user_id):
        db_util.delete_api_key(user_id)

    api_key = generate_new_api_key()
    return db_util.create_new_api_key(user_id, api_key)
