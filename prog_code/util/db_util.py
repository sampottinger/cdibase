"""Logic for interfacing with application's persistance mechanism.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import csv
import os
import sqlite3
import threading

import yaml

from ..struct import models

import file_util


class SharedConnection:
    """Singleton wrapper around a database connection.

    Singleton wrapper around a database connection that allows for sharing of
    that connection between multiple threads. Effectively acts as a database
    connection pool of 1.
    """

    instance = None

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = SharedConnection()
        return cls.instance

    def __init__(self):
        self.__connection = sqlite3.connect('./db/daxlab.db')
        self.__lock = threading.Lock()

    def cursor(self):
        self.__lock.acquire(True)
        return self.__connection.cursor()

    def commit(self):
        self.__connection.commit()

    def close(self):
        self.__lock.release()


def get_db_connection():
    """Get an open connection to the application database.

    @note: May come from connection pool.
    @return: Thread-safe connection to application database.
    @rtype: SharedConnection
    """
    return SharedConnection.get_instance()

def save_mcdi_model(newMetadataModel):
    """Save a metadata for a MCDI format.

    @param newMetadataModel: Model containing format metadata.
    @type newMetadataModel: models.MCDIFormatMetadata
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO mcdi_formats VALUES (?, ?, ?)",
        (
            newMetadataModel.human_name,
            newMetadataModel.safe_name,
            newMetadataModel.filename
        )
    )
    connection.commit()
    connection.close()


def delete_mcdi_model(metadataModelName):
    """Delete an existing saved MCDI format.

    @param metadataModelName: The name of the MCDI format to delete.
    @type metadataModelName: str
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM mcdi_formats WHERE safe_name=?",
        (metadataModelName,)
    )
    connection.commit()
    connection.close()


def load_mcdi_model_listing():
    """Load metadata for all MCDI formats.

    @return: Iterable over metadata for all MCDI formats..
    @rtype: Iterable over models.MCDIFormatMetadata
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM mcdi_formats"
    )
    ret_val = map(lambda x: models.MCDIFormatMetadata(x[0], x[1], x[2]), cursor)
    connection.close()
    return ret_val


def load_mcdi_model(name):
    """Load a complete MCDI format.

    @param name: The name of the MCDI format to load.
    @type name: str
    @return: MCDI format details and metadata.  None if MCDI format
        by the given name could not be found.
    @rtype: models.MCDIFormat
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        '''SELECT human_name,safe_name,filename FROM mcdi_formats
        WHERE safe_name=?''',
        (name,)
    )
    metadata = cursor.fetchone()
    connection.close()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        content = f.read()
    spec = yaml.load(content)

    return models.MCDIFormat(metadata[0], metadata[1], metadata[2], spec)


def save_presentation_model(newMetadataModel):
    """Save a presentation format.

    @param newMetadataModel: Model containing format metadata.
    @type newMetadataModel: models.PresentationFormatMetadata
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO presentation_formats VALUES (?, ?, ?)",
        (
            newMetadataModel.safe_name,
            newMetadataModel.human_name,
            newMetadataModel.filename
        )
    )
    connection.commit()
    connection.close()


def delete_presentation_model(metadataModelName):
    """Delete an existing saved presentation format.

    @param metadataModelName: The name of the presentation format to delete.
    @type metadataModelName: str
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM presentation_formats WHERE safe_name=?",
        (metadataModelName,)
    )
    connection.commit()
    connection.close()


def load_presentation_model_listing():
    """Load metadata for all presentation formats.

    @return: Iterable over metadata for all MCDI formats..
    @rtype: Iterable over models.PresentationFormatMetadata
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM presentation_formats"
    )
    ret_val = map(lambda x: models.PresentationFormatMetadata(x[0], x[1], x[2]),
        cursor)
    connection.close()
    return ret_val


def load_presentation_model(name):
    """Load a complete MCDI format.

    @param name: The name of the MCDI format to load.
    @type name: str
    @return: MCDI format details and metadata. None if presentation format
        by the given name could not be found.
    @rtype: models.PresentationFormat
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        '''SELECT human_name,safe_name,filename FROM presentation_formats
        WHERE safe_name=?''',
        (name,)
    )
    metadata = cursor.fetchone()
    connection.close()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        content = f.read()
    spec = yaml.load(content)

    return models.PresentationFormat(metadata[0], metadata[1], metadata[2],
        spec)


def save_percentile_model(newMetadataModel):
    """Save a table of values necessary for calcuating child MCDI percentiles.

    @param name: The name of the precentile table model to load.
    @type name: str
    @return: MCDI format details and metadata.
    @rtype: models.PercentileTableMetadata
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO percentile_tables VALUES (?, ?, ?)",
        (
            newMetadataModel.safe_name,
            newMetadataModel.human_name,
            newMetadataModel.filename
        )
    )
    connection.commit()
    connection.close()


def delete_percentile_model(metadataModelName):
    """Delete an existing saved percentile data table.

    @param metadataModelName: The name of the precentile table to delete.
    @type metadataModelName: str
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM percentile_tables WHERE safe_name=?",
        (metadataModelName,)
    )
    connection.commit()
    connection.close()


def load_percentile_model_listing():
    """Load metadata for all percentile tables.

    @return: Iterable over metadata for all percentile tables.
    @rtype: Iterable over models.PercentileTableMetadata
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM percentile_tables"
    )
    ret_val = map(lambda x: models.PercentileTableMetadata(x[0], x[1], x[2]),
        cursor)
    connection.close()
    return ret_val


def load_percentile_model(name):
    """Load a complete percentile table.

    @param name: The name of the percentile table to load.
    @type name: str
    @return: Percentile table contents and metadata. None if percentile table
        by the given name could not be found.
    @rtype: models.PercetileTable
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        '''SELECT human_name,safe_name,filename FROM percentile_tables
        WHERE safe_name=?''',
        (name,)
    )
    metadata = cursor.fetchone()
    connection.close()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        spec = list(csv.reader(f))

    return models.PercentileTable(metadata[0], metadata[1], metadata[2], spec)


def load_snapshot_contents(snapshot):
    """Load reports of individual statuses for words.

    Load status for individual / state of words as part of an MCDI snapshot.

    @param snapshot: The snapshot to get contents for.
    @type snapshot: model.SnapshotMetadata
    @return: Iterable over the details of the given MCDI snapshot.
    @rtype: Iterable over models.SnapshotContent
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM snapshot_content WHERE snapshot_id=?",
        (snapshot.database_id,)
    )
    ret_val = map(lambda x: models.SnapshotContent(*x), cursor.fetchall())
    connection.close()
    return ret_val


def load_user_model(identifier):
    """Load the user model for a user account with the given email address.

    @param identifier: The email of the user for which a user model should be
        retrieved. Can also be integer ID.
    @type email: str or int
    @return: The user account information for the user with the given email
        address. None if corresponding user account cannot be found.
    @rtype: models.User
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    if isinstance(identifier, basestring):
        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (identifier,)
        )
    else:
        cursor.execute(
            "SELECT * FROM users WHERE id=?",
            (identifier,)
        )
    result = cursor.fetchone()
    connection.close()
    if not result:
        return None
    return models.User(*(result))


def save_user_model(user, existing_email=None):
    """Save data about a user account.

    @param user: The user model to save to the database.
    @type user: models.User
    """
    if not existing_email:
        existing_email = user.email

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        '''UPDATE users SET email=?,password_hash=?,can_enter_data=?,
            can_edit_parents=?,can_access_data=?,can_change_formats=?,
            can_use_api_key=?,can_admin=? WHERE email=?''',
        (
            user.email,
            user.password_hash,
            user.can_enter_data,
            user.can_edit_parents,
            user.can_access_data,
            user.can_change_formats,
            user.can_use_api_key,
            user.can_admin,
            existing_email
        )
    )
    connection.commit()
    connection.close()


def create_user_model(user):
    """Create a new user account.

    @param user: The new user account to persist to the database.
    @type user: models.User
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        '''INSERT INTO users (email, password_hash, can_enter_data,
            can_edit_parents,can_access_data, can_change_formats,
            can_use_api_key, can_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            user.email,
            user.password_hash,
            user.can_enter_data,
            user.can_edit_parents,
            user.can_access_data,
            user.can_change_formats,
            user.can_use_api_key,
            user.can_admin
        )
    )
    connection.commit()
    connection.close()


def delete_user_model(email):
    """Delete the user account with the given email address.

    @param email: The email address of the user account to delete.
    @type email: str
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM users WHERE email=?",
        (email,)
    )
    connection.commit()
    connection.close()


def get_all_user_models():
    """Get a listing of all user accounts for the web application.

    @return: Iterable over user account information.
    @rtype: Iterable over models.User
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    ret_val = map(lambda x: models.User(*x), cursor.fetchall())
    connection.close()
    return ret_val


def lookup_global_participant_id(study_id, participant_study_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT child_id FROM snapshots WHERE study=? AND study_id=?",
        (study_id, participant_study_id)
    )
    ret_values = cursor.fetchone()
    if ret_values == None:
        connection.close()
        return None

    ret_val = ret_values[0]
    return ret_val


def get_api_key_by_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT api_key FROM api_keys WHERE user_id=?",
        (user_id,)
    )
    api_key = cursor.fetchone()
    connection.commit()
    connection.close()

    if api_key:
        return models.APIKey(user_id, api_key[0])
    else:
        return None


def get_api_key_by_key(api_key):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT user_id FROM api_keys WHERE api_key=?",
        (api_key,)
    )
    user_id = cursor.fetchone()
    connection.commit()
    connection.close()

    if user_id:
        return models.APIKey(user_id[0], api_key)
    else:
        return None


def get_api_key(identifier):
    if isinstance(identifier, basestring):
        return get_api_key_by_key(identifier)
    else:
        return get_api_key_by_user(identifier)


def delete_api_key(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM api_keys WHERE user_id=?",
        (user_id,)
    )
    connection.close()


def create_new_api_key(user_id, api_key):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO api_keys VALUES (?, ?)",
        (user_id, api_key)
    )
    connection.close()

    return models.APIKey(user_id, api_key)


# TODO: Combined for transaction
def insert_snapshot(snapshot_metadata, word_entries):
    connection = get_db_connection()
    cursor = connection.cursor()

    cmd = "INSERT INTO snapshots VALUES (%s)" % (", ".join("?" * 19))
    cursor.execute(
        cmd,
        (
            None,
            snapshot_metadata.child_id,
            snapshot_metadata.study_id,
            snapshot_metadata.study,
            snapshot_metadata.gender,
            snapshot_metadata.age,
            snapshot_metadata.birthday,
            snapshot_metadata.session_date,
            snapshot_metadata.session_num,
            snapshot_metadata.total_num_sessions,
            snapshot_metadata.words_spoken,
            snapshot_metadata.items_excluded,
            snapshot_metadata.percentile,
            snapshot_metadata.extra_categories,
            snapshot_metadata.revision,
            ",".join(snapshot_metadata.languages),
            snapshot_metadata.num_languages,
            snapshot_metadata.mcdi_type,
            snapshot_metadata.hard_of_hearing
        )
    )
    new_snapshot_id = cursor.lastrowid
    snapshot_metadata.database_id=new_snapshot_id

    # Put in snapshot contents
    for (word, val) in word_entries.items():
        cursor.execute(
            "INSERT INTO snapshot_content VALUES (?, ?, ?, ?)",
            (
                new_snapshot_id,
                word,
                val,
                0
            )
        )

    connection.commit()
    connection.close()


def insert_parent_form(form_metadata):
    connection = get_db_connection()
    cursor = connection.cursor()

    cmd = "INSERT INTO parent_forms VALUES (%s)" % (", ".join("?" * 14))
    cursor.execute(
        cmd,
        (
            form_metadata.form_id,
            form_metadata.child_name,
            form_metadata.parent_email,
            form_metadata.mcdi_type,
            form_metadata.database_id,
            form_metadata.study_id,
            form_metadata.study,
            form_metadata.gender,
            form_metadata.birthday,
            form_metadata.items_excluded,
            form_metadata.extra_categories,
            form_metadata.languages,
            form_metadata.num_languages,
            form_metadata.hard_of_hearing
        )
    )

    connection.commit()
    connection.close()


def get_parent_form_by_id(form_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM parent_forms WHERE form_id=?",
        (form_id,)
    )
    form_info = cursor.fetchone()
    connection.commit()
    connection.close()

    if form_info:
        return models.ParentForm(*form_info)
    else:
        return None


def remove_parent_form(form_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM parent_forms WHERE form_id=?",
        (form_id,)
    )
    form_info = cursor.fetchone()
    connection.commit()
    connection.close()
