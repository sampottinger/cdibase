"""Logic for managing user API keys and other minuta.

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

import db_util
import user_util


def interp_csv_field(csv_field):
    """Interpret a simple comma seperated string as a list of string values.

    Interpret a simple string that deliminates values by commas (no quoting
    or escape characters allowed.

    @param csv_field: The string to interpret.
    @type csv_field: str
    @return: CSV string interpreted as a list of values.
    @rtype: list
    """
    if csv_field == '':
        return []
    else:
        return csv_field.split(',')


def get_list_item_if_avail(target_list, index, default_value=''):
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
        found = db_util.read_api_key_model_record(new_key) == None

    return new_key


def read_api_key_model(user_id):
    """Get the API key for a given user.

    @param user_id: The database id of the user to get the API key for.
    @type user_id: int
    @return: API key assigned to the given user or None if not found.
    @rtype: str
    """
    return db_util.read_api_key_model_record(user_id)


def create_api_key_model(user_id):
    """Create a new API key and assign it to the given user.

    Create a new randomly generated API key for the given user, assigning the
    newly generated API key to the user with the given user_id.

    @param user_id: The ID of the user to generate the key for.
    @type user_id: int
    @return: The newly generated API key.
    @rtype: str
    """
    if read_api_key_model(user_id):
        db_util.delete_api_key_model(user_id)

    api_key = generate_new_api_key()
    return db_util.create_api_key_model(user_id, api_key)
