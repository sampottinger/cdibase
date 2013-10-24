"""Logic for managing user API keys and other minuta.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import db_util
import user_util


def interp_csv_field(target):
    """Interpret a simple comma seperated string as a list of string values.

    Interpret a simple string that deliminates values by commas (no quoting
    or escape characters allowed.

    @param target: The string to interpret.
    @type target: str
    @return: CSV string interpreted as a list of values.
    @rtype: list
    """
    if target == '':
        return []
    else:
        return target.split(',')


def get_if_avail(target_list, index, default_value=''):
    """Get a value from a list if that item is available.

    @param target_list: The list to try to get an item from.
    @type target_list: list
    @param index: The index of the item to get from the list.
    @type index: int
    @keyword default_value: The value to return if the given item is not found
        in the specifed collection.
    """
    if len(target_list) > index:
        return target_list[index]
    else:
        return default_value


def generate_new_api_key():
    """Generate a new unique API key.

    Generate a unique random API key that has not been assigned to any other
    system users.

    @return: The newly generated API key.
    @rtype: str
    """
    found = False
    new_key = None

    while not found: 
        new_key = user_util.generate_password(pass_len=20).lower()
        found = db_util.get_api_key(new_key) == None

    return new_key


def get_api_key(user_id):
    """Get the API key for a given user.

    @param user_id: The database id of the user to get the API key for.
    @type user_id: int
    @return: API key assigned to the given user or None if not found.
    @rtype: str
    """
    return db_util.get_api_key(user_id)


def create_new_api_key(user_id):
    """Create a new API key and assign it to the given user.

    Create a new randomly generated API key for the given user, assigning the
    newly generated API key to the user with the given user_id.

    @param user_id: The ID of the user to generate the key for.
    @type user_id: int
    @return: The newly generated API key.
    @rtype: str
    """
    if get_api_key(user_id):
        db_util.delete_api_key(user_id)

    api_key = generate_new_api_key()
    return db_util.create_new_api_key(user_id, api_key)
