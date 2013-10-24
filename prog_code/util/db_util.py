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
        """Get a shared instance of this database connection singleton.

        Get a shared instance of this class-wide singleton that encloses a
        connection to the application sqlite database.

        @return: The shared singleton instance with a databae connection.
        @rtype: SharedConnection
        """
        if not cls.instance:
            cls.instance = SharedConnection()
        return cls.instance

    def __init__(self):
        """Create a new instance of the SharedConnection singleton.

        Create a new instance of the SharedConnection database connection
        wrapper / singleton. This should only be called by SharedConnection
        itself.
        """
        self.__connection = sqlite3.connect('./db/daxlab.db')
        self.__lock = threading.Lock()

    def cursor(self):
        """With thread-saftey, acquire a database cursor for the application DB.

        @return: Cursor for the application database.
        @rtype: sqlite3 database cursor
        """
        self.__lock.acquire(True)
        return self.__connection.cursor()

    def commit(self):
        """Commit changes made to the database.

        Commit / save changes made to the database. This must be called for
        changes to be persisted.
        """
        self.__connection.commit()

    def close(self):
        """Release the current thread's aquired connection.

        Release the current thread's acquired connection back to the connection
        pool.
        """
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
        'INSERT INTO mcdi_formats VALUES (?, ?, ?)',
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
        'DELETE FROM mcdi_formats WHERE safe_name=?',
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
        'SELECT human_name,safe_name,filename FROM mcdi_formats'
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
        'INSERT INTO presentation_formats VALUES (?, ?, ?)',
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
        'DELETE FROM presentation_formats WHERE safe_name=?',
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
        'SELECT human_name,safe_name,filename FROM presentation_formats'
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
        'INSERT INTO percentile_tables VALUES (?, ?, ?)',
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
        'DELETE FROM percentile_tables WHERE safe_name=?',
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
        'SELECT human_name,safe_name,filename FROM percentile_tables'
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
        'SELECT * FROM snapshot_content WHERE snapshot_id=?',
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
            'SELECT * FROM users WHERE email=?',
            (identifier,)
        )
    else:
        cursor.execute(
            'SELECT * FROM users WHERE id=?',
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
        'DELETE FROM users WHERE email=?',
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
    cursor.execute('SELECT * FROM users')
    ret_val = map(lambda x: models.User(*x), cursor.fetchall())
    connection.close()
    return ret_val


def lookup_global_participant_id(study, participant_study_id):
    """Get the global participant ID given study information.

    Get the global participant ID for a child given that child's study ID and
    participant study ID.

    @param study: The name of the study to find the child in.
    @type study: str
    @param participant_study_id: The ID of the target child in that study.
    @type participant_study_id: str
    @return: The participant's global ID if the child was located in the
        database. Returns None otherwise.
    @rtype: int
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'SELECT child_id FROM snapshots WHERE study=? AND study_id=?',
        (study, participant_study_id)
    )
    ret_values = cursor.fetchone()
    if ret_values == None:
        connection.close()
        return None

    ret_val = ret_values[0]
    return ret_val


def get_api_key_by_user(user_id):
    """Get the API key for a user.

    @param user_id: The ID of a user account. This function will return the API
        key assigned to this user account.
    @type user_id: int
    @return: Record for the API key assigned to that user or None if a key has
        not been assigned to that user.
    @rtype: models.APIKey
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'SELECT api_key FROM api_keys WHERE user_id=?',
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
    """Get the record for an API key.

    @param api_key: The API key to find a record for.
    @type api_key: str
    @return: The API key record for the given API key. None if the provided API
        key could not be found.
    @rtype: models.APIKey
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'SELECT user_id FROM api_keys WHERE api_key=?',
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
    """Get the record for an API key for a user ID or the API key iteself.

    Given either an integer user ID or a string API key, this function returns
    the API key record for that user or that string key.

    @param identifier: Either a string API key or an integer user ID.
    @type identifier: int or str
    @return: The API key record for the provided user or string key. Returns
        None if the provided user cannot be found, that user does not have an
        API key, or the key could not be found in the database.
    @rtype: models.APIKey
    """
    if isinstance(identifier, basestring):
        return get_api_key_by_key(identifier)
    else:
        return get_api_key_by_user(identifier)


def delete_api_key(user_id):
    """Delete a record of an API key for a user.

    @param user_id: The integer ID of the user to delete an API key for.
    @type user_id: int
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'DELETE FROM api_keys WHERE user_id=?',
        (user_id,)
    )
    connection.close()


def create_new_api_key(user_id, api_key):
    """Create a new record of an API key.

    @param user_id: The integer ID of the user to create an API key record for.
    @type user_id: int
    @param api_key: The string API key to assign to this user.
    @type api_key: str
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO api_keys VALUES (?, ?)',
        (user_id, api_key)
    )
    connection.close()

    return models.APIKey(user_id, api_key)


# TODO: Combined for transaction
def insert_snapshot(snapshot_metadata, word_entries):
    """Insert a new MCDI snapshot.

    @param snapshot_metadata: The metadata for this snapshot that should be
        saved along with individual word entries.
    @type snapshot_metadata: models.SnapshotMetadata
    @param word_entries: Collection of records indicating what words were
        spoken and what words were not. Keys should be words and values are
        status indicators showing if those words were spoken or not.
    @type: dict
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    if snapshot_metadata.child_id == None:
        cursor.execute('SELECT MAX(child_id) FROM snapshots')
        child_id = cursor.fetchone()[0] + 1
    else:
        child_id = snapshot_metadata.child_id

    cmd = 'INSERT INTO snapshots VALUES (%s)' % (', '.join('?' * 19))
    cursor.execute(
        cmd,
        (
            None,
            child_id,
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
            ','.join(snapshot_metadata.languages),
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
            'INSERT INTO snapshot_content VALUES (?, ?, ?, ?)',
            (
                new_snapshot_id,
                word.lower(),
                val,
                0
            )
        )

    connection.commit()
    connection.close()


def insert_parent_form(form_metadata):
    """Create a record of a parent form.

    @param form_metadata: Information about the parent form to persist.
    @type form_metadata: models.ParentForm
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    cmd = 'INSERT INTO parent_forms VALUES (%s)' % (', '.join('?' * 14))
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
    """Get information about a parent MCDI form.

    @param form_id: The ID of the parent MCDI form to get the record for.
    @type form_id: str
    @return: The ParentForm corresponding to the provided ID or None if that
        form could not be found.
    @rtype: models.ParentForm
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'SELECT * FROM parent_forms WHERE form_id=?',
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
    """Delete the record of a parent MCDI form.

    @param form_id: The ID of the parent MCDI form to delete.
    @type form_id: str
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        'DELETE FROM parent_forms WHERE form_id=?',
        (form_id,)
    )
    form_info = cursor.fetchone()
    connection.commit()
    connection.close()
