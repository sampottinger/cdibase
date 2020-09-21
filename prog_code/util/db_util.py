"""Logic for interfacing with application's persistance mechanism.

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

import csv
import datetime
import os
import json
import sqlite3
import threading
import time
import typing

import yaml

from ..struct import models

import prog_code.util.constants as constants
import prog_code.util.file_util as file_util

OptionalCursor = typing.Optional[sqlite3.Cursor]

SNAPSHOT_METADATA_COLS = [
    'id',
    'child_id',
    'study_id',
    'study',
    'gender',
    'age',
    'birthday',
    'session_date',
    'session_num',
    'total_num_sessions',
    'words_spoken',
    'items_excluded',
    'percentile',
    'extra_categories',
    'revision',
    'languages',
    'num_languages',
    'cdi_type',
    'hard_of_hearing',
    'deleted'
]


class SharedConnection:
    """Singleton wrapper around a database connection.

    Singleton wrapper around a database connection that allows for sharing of
    that connection between multiple threads. Effectively acts as a database
    connection pool of 1.
    """

    instance = None

    @classmethod
    def get_instance(cls) -> 'SharedConnection':
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
        self.__connection = sqlite3.connect('./db/cdi.db')
        self.__lock = threading.Lock()

    def cursor(self) -> sqlite3.Cursor:
        """With thread-saftey, acquire a database cursor for the application DB.

        @return: Cursor for the application database.
        @rtype: sqlite3 database cursor
        """
        self.__lock.acquire(True)
        return self.__connection.cursor()

    def commit(self) -> None:
        """Commit changes made to the database.

        Commit / save changes made to the database. This must be called for
        changes to be persisted.
        """
        self.__connection.commit()

    def close(self) -> None:
        """Release the current thread's aquired connection.

        Release the current thread's acquired connection back to the connection
        pool.
        """
        self.__lock.release()


class RealizedCursor:

    def __init__(self, cursor: OptionalCursor):
        """Use a default DB cursor if the cursor is not given.

        @param cursor: The cursor to prefer. If None, will create a default.
        @returns: Given cursor if cursor_maybe != None or, otherwise, a default
            cursor.
        """
        cursor_realized: sqlite3.Cursor

        self.__cursor_provided = cursor != None
        if self.__cursor_provided:
            cursor_realized = cursor # type: ignore
        else:
            self.__connection = get_db_connection()
            cursor_realized = self.__connection.cursor()

        self.__cursor = cursor_realized

    def __enter__(self) -> sqlite3.Cursor:
        """Provide the realized cursor to the target function.

        @returns: Realized cursor.
        """
        return self.__cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the cursor allocation if it was needed."""
        if not self.__cursor_provided:
            self.__connection.commit()
            self.__connection.close()


def get_db_connection() -> SharedConnection:
    """Get an open connection to the application database.

    @note: May come from connection pool.
    @return: Thread-safe connection to application database.
    @rtype: SharedConnection
    """
    return SharedConnection.get_instance()


def save_cdi_model(newMetadataModel: models.CDIFormatMetadata,
        cursor_maybe: OptionalCursor = None) -> None:
    """Save a metadata for a CDI format.

    @param newMetadataModel: Model containing format metadata.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'INSERT INTO cdi_formats VALUES (?, ?, ?)',
            (
                newMetadataModel.human_name,
                newMetadataModel.safe_name,
                newMetadataModel.filename
            )
        )


def delete_cdi_model(metadataModelName: str,
        cursor_maybe: OptionalCursor = None) -> None:
    """Delete an existing saved CDI format.

    @param metadataModelName: The name of the CDI format to delete.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'DELETE FROM cdi_formats WHERE safe_name=?',
            (metadataModelName,)
        )


def load_cdi_model_listing(
        cursor_maybe: OptionalCursor = None) -> typing.List[models.CDIFormatMetadata]:
    """Load metadata for all CDI formats.

    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Iterable over metadata for all CDI formats.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT human_name,safe_name,filename FROM cdi_formats'
        )
        ret_val = list(map(
            lambda x: models.CDIFormatMetadata(x[0], x[1], x[2]),
            cursor
        ))

    return ret_val


def load_cdi_model(name: str,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.CDIFormat]:
    """Load a complete CDI format.

    @param name: The name of the CDI format to load.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: CDI format details and metadata. None if CDI format
        by the given name could not be found.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''SELECT human_name,safe_name,filename FROM cdi_formats
            WHERE safe_name=?''',
            (name.replace(" ", ""),)
        )
        metadata = cursor.fetchone()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        content = f.read()
    spec = yaml.safe_load(content)

    return models.CDIFormat(metadata[0], metadata[1], metadata[2], spec)


def save_presentation_model(
        newMetadataModel: models.PresentationFormatMetadata,
        cursor_maybe: OptionalCursor = None) -> None:
    """Save a presentation format.

    @param newMetadataModel: Model containing format metadata.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'INSERT INTO presentation_formats VALUES (?, ?, ?)',
            (
                newMetadataModel.safe_name,
                newMetadataModel.human_name,
                newMetadataModel.filename
            )
        )


def delete_presentation_model(metadataModelName: str,
        cursor_maybe: OptionalCursor = None) -> None:
    """Delete an existing saved presentation format.

    @param metadataModelName: The name of the presentation format to delete.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'DELETE FROM presentation_formats WHERE safe_name=?',
            (metadataModelName,)
        )


def load_presentation_model_listing(
        cursor_maybe: OptionalCursor = None) -> typing.List[models.PresentationFormatMetadata]:
    """Load metadata for all presentation formats.

    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Iterable over metadata for all CDI formats.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT human_name,safe_name,filename FROM presentation_formats'
        )
        ret_val = list(map(
            lambda x: models.PresentationFormatMetadata(x[0], x[1], x[2]),
            cursor
        ))

    return ret_val


def load_presentation_model(
        name: str,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.PresentationFormat]:
    """Load a complete CDI format.

    @param name: The name of the CDI format to load.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: CDI format details and metadata. None if presentation format
        by the given name could not be found.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            SELECT
                human_name,
                safe_name,
                filename
            FROM
                presentation_formats
            WHERE
                safe_name=?
            ''',
            (name,)
        )
        metadata = cursor.fetchone()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        content = f.read()
    spec = yaml.safe_load(content)

    return models.PresentationFormat(
        metadata[0],
        metadata[1],
        metadata[2],
        spec
    )


def save_percentile_model(
        newMetadataModel: models.PercentileTableMetadata,
        cursor_maybe: OptionalCursor = None) -> None:
    """Save a table of values necessary for calcuating child CDI percentiles.

    @param newMetadataModel: CDI format details and metadata.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'INSERT INTO percentile_tables VALUES (?, ?, ?)',
            (
                newMetadataModel.safe_name,
                newMetadataModel.human_name,
                newMetadataModel.filename
            )
        )


def delete_percentile_model(metadataModelName: str,
        cursor_maybe: OptionalCursor = None) -> None:
    """Delete an existing saved percentile data table.

    @param metadataModelName: The name of the precentile table to delete.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'DELETE FROM percentile_tables WHERE safe_name=?',
            (metadataModelName,)
        )


def load_percentile_model_listing(
        cursor_maybe: OptionalCursor = None) -> typing.List[models.PercentileTableMetadata]:
    """Load metadata for all percentile tables.

    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Iterable over metadata for all percentile tables.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT human_name,safe_name,filename FROM percentile_tables'
        )
        ret_val = list(map(
            lambda x: models.PercentileTableMetadata(x[0], x[1], x[2]),
            cursor
        ))

    return ret_val


def load_percentile_model(name: str,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.PercentileTable]:
    """Load a complete percentile table.

    @param name: The name of the percentile table to load.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Percentile table contents and metadata. None if percentile table
        by the given name could not be found.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''SELECT human_name,safe_name,filename FROM percentile_tables
            WHERE safe_name=?''',
            (name,)
        )
        metadata = cursor.fetchone()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        inner_spec = csv.reader(f)
        spec = [[float(x) if x != '%' else 0 for x in row] for row in inner_spec]

    return models.PercentileTable(metadata[0], metadata[1], metadata[2], spec)


def list_stuides(cursor_maybe: OptionalCursor = None) -> typing.List[str]:
    """Get the name of all studies available in the application.

    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: List of study names.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT DISTINCT study FROM snapshots WHERE deleted = 0',
        )
        ret_val = list(map(lambda x: x[0], cursor.fetchall()))

    return ret_val


def load_snapshot_contents(snapshot: models.SnapshotMetadata,
        cursor_maybe: OptionalCursor = None) -> typing.List[models.SnapshotContent]:
    """Load reports of individual statuses for words.

    Load status for individual / state of words as part of an CDI snapshot.

    @param snapshot: The snapshot to get contents for.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Iterable over the details of the given CDI snapshot.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT * FROM snapshot_content WHERE snapshot_id=?',
            (snapshot.database_id,)
        )
        ret_val = list(map(
            lambda x: models.SnapshotContent(*x),
            cursor.fetchall()
        ))

    return ret_val


def load_user_model(
        identifier: typing.Union[int, str],
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.User]:
    """Load the user model for a user account with the given email address.

    @param identifier: The email of the user for which a user model should be
        retrieved. Can also be integer ID.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: The user account information for the user with the given email
        address. None if corresponding user account cannot be found.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        if isinstance(identifier, str):
            cursor.execute(
                '''
                SELECT
                    id,
                    email,
                    password_hash,
                    can_enter_data,
                    can_delete_data,
                    can_import_data,
                    can_edit_parents,
                    can_access_data,
                    can_change_formats,
                    can_use_api_key,
                    can_admin
                FROM
                    users
                WHERE
                    email=?
                ''',
                (identifier,)
            )
        else:
            cursor.execute(
                '''
                SELECT
                    id,
                    email,
                    password_hash,
                    can_enter_data,
                    can_delete_data,
                    can_import_data,
                    can_edit_parents,
                    can_access_data,
                    can_change_formats,
                    can_use_api_key,
                    can_admin
                FROM
                    users
                WHERE
                    id=?
                ''',
                (identifier,)
            )
        result = cursor.fetchone()

    if not result:
        return None
    return models.User(*(result))


def save_user_model(
        user: models.User,
        existing_email: typing.Optional[str] = None,
        cursor_maybe: OptionalCursor = None) -> None:
    """Save data about a user account.

    @param user: The user model to save to the database.
    @param existing_email: Prior email for user.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    if not existing_email:
        existing_email = user.email

    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            UPDATE
                users
            SET
                email=?,
                password_hash=?,
                can_enter_data=?,
                can_delete_data=?,
                can_import_data=?,
                can_edit_parents=?,
                can_access_data=?,
                can_change_formats=?,
                can_use_api_key=?,
                can_admin=?
            WHERE
                email=?
            ''',
            (
                user.email,
                user.password_hash,
                user.can_enter_data,
                user.can_delete_data,
                user.can_import_data,
                user.can_edit_parents,
                user.can_access_data,
                user.can_change_formats,
                user.can_use_api_key,
                user.can_admin,
                existing_email
            )
        )


def create_user_model(user: models.User,
        cursor_maybe: OptionalCursor = None) -> None:
    """Create a new user account.

    @param user: The new user account to persist to the database.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''INSERT INTO users (email, password_hash, can_enter_data,
                can_delete_data, can_import_data, can_edit_parents, can_access_data,
                can_change_formats, can_use_api_key, can_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                user.email,
                user.password_hash,
                user.can_enter_data,
                user.can_import_data,
                user.can_delete_data,
                user.can_edit_parents,
                user.can_access_data,
                user.can_change_formats,
                user.can_use_api_key,
                user.can_admin
            )
        )


def delete_user_model(email: str, cursor_maybe: OptionalCursor = None) -> None:
    """Delete the user account with the given email address.

    @param email: The email address of the user account to delete.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'DELETE FROM users WHERE email=?',
            (email,)
        )


def get_all_user_models(
        cursor_maybe: OptionalCursor = None) -> typing.List[models.User]:
    """Get a listing of all user accounts for the web application.

    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Iterable over user account information.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            SELECT
                id,
                email,
                password_hash,
                can_enter_data,
                can_delete_data,
                can_import_data,
                can_edit_parents,
                can_access_data,
                can_change_formats,
                can_use_api_key,
                can_admin
            FROM
                users
            '''
        )
        ret_val = list(map(lambda x: models.User(*x), cursor.fetchall()))

    return ret_val


def lookup_global_participant_id(
        study: str,
        participant_study_id: str,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[int]:
    """Get the global participant ID given study information.

    Get the global participant ID for a child given that child's study ID and
    participant study ID.

    @param study: The name of the study to find the child in.
    @param participant_study_id: The ID of the target child in that study.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: The participant's global ID if the child was located in the
        database. Returns None otherwise.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT child_id FROM snapshots WHERE study=? AND study_id=?',
            (study, participant_study_id)
        )
        ret_values = cursor.fetchone()

    if ret_values == None:
        return None

    ret_val = ret_values[0]
    return ret_val


def get_api_key_by_user(user_id: int,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.APIKey]:
    """Get the API key for a user.

    @param user_id: The ID of a user account. This function will return the API
        key assigned to this user account.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: Record for the API key assigned to that user or None if a key has
        not been assigned to that user.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT api_key FROM api_keys WHERE user_id=?',
            (user_id,)
        )
        api_key = cursor.fetchone()

    if api_key:
        return models.APIKey(user_id, api_key[0])
    else:
        return None


def get_api_key_by_key(api_key: str,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.APIKey]:
    """Get the record for an API key.

    @param api_key: The API key to find a record for.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @return: The API key record for the given API key. None if the provided API
        key could not be found.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT user_id FROM api_keys WHERE api_key=?',
            (api_key,)
        )
        user_id = cursor.fetchone()

    if user_id:
        return models.APIKey(user_id[0], api_key)
    else:
        return None


def get_api_key(
        identifier: typing.Union[int, str]) -> typing.Optional[models.APIKey]:
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
    if isinstance(identifier, str):
        return get_api_key_by_key(identifier)
    else:
        return get_api_key_by_user(identifier)


def delete_api_key(user_id: int, cursor_maybe: OptionalCursor = None) -> None:
    """Delete a record of an API key for a user.

    @param user_id: The integer ID of the user to delete an API key for.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'DELETE FROM api_keys WHERE user_id=?',
            (user_id,)
        )


def create_new_api_key(user_id: int, api_key: str) -> models.APIKey:
    """Create a new record of an API key.

    @param user_id: The integer ID of the user to create an API key record for.
    @type user_id: int
    @param api_key: The string API key to assign to this user.
    @type api_key: str
    @returns: Newly created API key record.
    """
    with get_cursor() as cursor:
        cursor.execute(
            'INSERT INTO api_keys VALUES (?, ?)',
            (user_id, api_key)
        )

    return models.APIKey(user_id, api_key)


def clean_up_date(target_val: str) -> typing.Optional[str]:
    """Standardize string date format to YYYY/MM/DD

    @param target_val: The value to standardize.
    @returns: Standardized string date serialization or None if target_val is
        invalid.
    """
    parts = target_val.split('/')
    if len(parts) != 3:
        return None

    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
    except ValueError:
        return None

    invalid_date = year < 1000
    invalid_date = invalid_date or month < 0 or month > 12
    invalid_date = invalid_date or day > 31 or day < 0
    if invalid_date:
        return None

    return '%d/%02d/%02d' % (year, month, day)


def clean_up_date_force(target_val: str) -> str:
    """Standardize string date format to YYYY/MM/DD and assert correct format.

    @param target_val: The value to standardize.
    @returns: Standardized string date serialization.
    """
    ret_val = clean_up_date(target_val)
    assert ret_val != None
    return ret_val # type: ignore


def get_realized_cursor(
        cursor: OptionalCursor) -> RealizedCursor:
    """Ensure a cursor is available.

    @param cursor: The cursor to prefer. If None, will create a default.
    """
    return RealizedCursor(cursor)


def get_cursor() -> RealizedCursor:
    """Get the default cursor.

    @returns: Default database cursor.
    """
    return get_realized_cursor(None)


def update_participant_metadata(child_id: str, gender: int, birthday_str: str,
        hard_of_hearing: int, languages: typing.Iterable[str],
        snapshot_ids: typing.Iterable[dict] = None,
        cursor: sqlite3.Cursor = None) -> None:
    """Update the participant metadata for all their snapshots.

    Update the "transient" metadata (metadata more likely needed to be changed
    due to clerical error or new information based on user interviews) for a
    participant across all of his or her snapshots.

    @param child_id: The global database ID of the participant whose snapshots
        should be updated.
    @param gender: Constant indicating the gender of the participant (male,
        female, or other) that corresponds to variables in the constants module.
    @type gender: int
    @param birthday_str: The string indicating the birthday of the participant
        as an ISO 8601 string without the time components.
    @type birthday_str: str
    @param hard_of_hearing: Constant indicating the hard of hearing status for a
        participant. Should correspond to a constant in the constants module.
    @type hard_of_hearing: int
    @param languages: Comma separated list of languages the participant speaks.
    @type languages: list of str
    """
    with get_realized_cursor(cursor) as cursor_realized:
        cols = ['gender', 'birthday', 'hard_of_hearing', 'languages']
        cmd_template = None
        if snapshot_ids:
            cmd_template = 'UPDATE snapshots SET %s WHERE child_id=? AND '
            cmd_template += 'study=? AND session_num=?'
        else:
            cmd_template = 'UPDATE snapshots SET %s WHERE child_id=?'

        params: typing.Tuple

        col_statements = map(lambda x: x + '=?', cols)
        col_strs = ','.join(col_statements)
        cmd_final = cmd_template % col_strs
        run_metadata_update = lambda params: cursor_realized.execute(
            cmd_final,
            params
        )

        if snapshot_ids:
            for snapshot_id in snapshot_ids:
                params = (gender, birthday_str, hard_of_hearing,
                    ','.join(languages), child_id, snapshot_id['study'],
                    snapshot_id['id'])
                run_metadata_update(params)
        else:
            params = (
                gender,
                birthday_str,
                hard_of_hearing,
                ','.join(languages),
                child_id
            )
            run_metadata_update(params)


def reserve_child_id(cursor: OptionalCursor = None) -> str:
    """Reserve a unique child ID.

    @param cursor: The cursor to use to execute the operation or None if one should be created.
    @returns: New child id.
    """
    with get_realized_cursor(cursor) as cursor_realized:
        cmd = 'INSERT INTO reservation VALUES (?)'
        cursor_realized.execute(
            cmd,
            (int(time.time()),)
        )
        new_id = cursor_realized.lastrowid
        return 'auto_%d' % new_id


def update_snapshot(snapshot_metadata: models.SnapshotMetadata,
        cursor: OptionalCursor = None) -> None:
    """Update the participant metadata for all their snapshots.

    Update the "transient" metadata (metadata more likely needed to be changed
    due to clerical error or new information based on user interviews) for a
    participant across all of his or her snapshots.

    @param snapshot_metadata: The metadata to update.
    @param cursor: The cursor to use to execute the operation.
    """
    with get_realized_cursor(cursor) as cursor_realized:
        if snapshot_metadata.child_id == None:
            child_id = reserve_child_id(cursor)
        else:
            child_id = snapshot_metadata.child_id # type: ignore

        # Standardize date
        snapshot_metadata.birthday = clean_up_date_force(snapshot_metadata.birthday)
        snapshot_metadata.session_date = clean_up_date_force(
            snapshot_metadata.session_date
        )

        if isinstance(snapshot_metadata.languages, str):
            raise RuntimeError('Languages must be a list.')

        languages_val = ','.join(snapshot_metadata.languages)

        non_db_id_cols = SNAPSHOT_METADATA_COLS[1:]
        col_statements = map(lambda x: x + '=?', non_db_id_cols)
        cmd = 'UPDATE snapshots SET %s WHERE id=?' % ','.join(col_statements)
        cursor_realized.execute(
            cmd,
            (
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
                languages_val,
                snapshot_metadata.num_languages,
                snapshot_metadata.cdi_type,
                snapshot_metadata.hard_of_hearing,
                snapshot_metadata.deleted,
                snapshot_metadata.database_id
            )
        )



def delete_snapshot(snapshot_id: int,
        cursor_maybe: OptionalCursor = None) -> None:
    """Hard delete a snapshot given its id.

    @param snapshot_id: The ID of the snapshot to delete.
    @param cursor_maybe: The cursor to use in executing the operation or None if
        a new cursor should be created.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''DELETE FROM snapshots WHERE id = ?''',
            (snapshot_id,)
        )
        cursor.execute(
            '''DELETE FROM snapshot_content WHERE snapshot_id = ?''',
            (snapshot_id,)
        )


# TODO: Combined for transaction
def insert_snapshot(snapshot_metadata: models.SnapshotMetadata,
        word_entries: typing.Union[
            typing.Mapping[str, int],
            typing.Iterable[models.SnapshotContent]
        ],
        cursor : OptionalCursor = None) -> None:
    """Insert a new CDI snapshot.

    @param snapshot_metadata: The metadata for this snapshot that should be
        saved along with individual word entries.
    @type snapshot_metadata: models.SnapshotMetadata
    @param word_entries: Collection of records indicating what words were
        spoken and what words were not. If dict, keys should be words and values
        are status indicators showing if those words were spoken or not.
        Othwerwise should be collection of models.SnapshotContent
    @type: dict or list
    """
    with get_realized_cursor(cursor) as cursor_realized:
        if snapshot_metadata.child_id == None:
            cursor_realized.execute('SELECT MAX(child_id) FROM snapshots')
            child_id = cursor_realized.fetchone()[0] + 1
        else:
            child_id = snapshot_metadata.child_id

        # Standardize date
        snapshot_metadata.birthday = clean_up_date_force(snapshot_metadata.birthday)
        snapshot_metadata.session_date = clean_up_date_force(
            snapshot_metadata.session_date
        )

        if isinstance(snapshot_metadata.languages, str):
            raise RuntimeError('Languages must be a list.')

        languages_val = ','.join(snapshot_metadata.languages)

        cmd = 'INSERT INTO snapshots VALUES (%s)' % (', '.join('?' * 20))
        cursor_realized.execute(
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
                languages_val,
                snapshot_metadata.num_languages,
                snapshot_metadata.cdi_type,
                snapshot_metadata.hard_of_hearing,
                snapshot_metadata.deleted
            )
        )
        new_snapshot_id = cursor_realized.lastrowid
        snapshot_metadata.database_id=new_snapshot_id

        # Put in snapshot contents
        if type(word_entries) is dict:
            word_entries_dict: dict
            word_entries_dict = word_entries # type: ignore
            for (word, val) in word_entries_dict.items():
                cursor_realized.execute(
                    'INSERT INTO snapshot_content VALUES (?, ?, ?, ?)',
                    (
                        new_snapshot_id,
                        word.lower(),
                        val,
                        0
                    )
                )
        else:
            word_entries_obj: typing.Iterable[models.SnapshotContent]
            word_entries_obj = word_entries # type: ignore
            for word_entry in word_entries_obj:
                cursor_realized.execute(
                    'INSERT INTO snapshot_content VALUES (?, ?, ?, ?)',
                    (
                        new_snapshot_id,
                        word_entry.word.lower(),
                        word_entry.value,
                        word_entry.revision
                    )
                )


def insert_parent_form(form_metadata: models.ParentForm,
        cursor_maybe: OptionalCursor = None) -> None:
    """Create a record of a parent form.

    @param form_metadata: Information about the parent form to persist.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """

    with get_realized_cursor(cursor_maybe) as cursor:
        cmd = 'INSERT INTO parent_forms VALUES (%s)' % (', '.join('?' * 15))
        cursor.execute(
            cmd,
            (
                form_metadata.form_id,
                form_metadata.child_name,
                form_metadata.parent_email,
                form_metadata.cdi_type,
                form_metadata.database_id,
                form_metadata.study_id,
                form_metadata.study,
                form_metadata.gender,
                form_metadata.birthday,
                form_metadata.items_excluded,
                form_metadata.extra_categories,
                form_metadata.languages,
                form_metadata.num_languages,
                form_metadata.hard_of_hearing,
                form_metadata.total_num_sessions
            )
        )


def get_parent_form_by_id(form_id: str,
        cursor_maybe: OptionalCursor = None) -> typing.Optional[models.ParentForm]:
    """Get information about a parent CDI form.

    @param form_id: The ID of the parent CDI form to get the record for.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @returns: The ParentForm corresponding to the provided ID or None if that
        form could not be found.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'SELECT * FROM parent_forms WHERE form_id=?',
            (form_id,)
        )
        form_info = cursor.fetchone()

    if form_info:
        return models.ParentForm(*form_info)
    else:
        return None


def remove_parent_form(form_id: str,
        cursor_maybe: OptionalCursor = None) -> None:
    """Delete the record of a parent CDI form.

    @param form_id: The ID of the parent CDI form to delete.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'DELETE FROM parent_forms WHERE form_id=?',
            (form_id,)
        )


def get_counts(cursor_maybe: OptionalCursor = None) -> typing.Mapping[str, typing.Mapping[str, int]]:
    """Get the number of CDIs completed by study by child ID.

    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @returns: Nested dictionary where outer key is child id and inner key is
        study.
    """
    by_study: typing.Dict[str, typing.Dict[str, int]]
    by_study = {}

    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute('SELECT study,child_id FROM snapshots WHERE deleted=0')

        metadata = cursor.fetchone()
        while metadata != None:

            study = metadata[0]
            child_id = metadata[1]
            if not study in by_study:
                by_study[study] = {}

            study_info = by_study[study]
            if not child_id in study_info:
                study_info[child_id] = 0

            study_info[child_id] = study_info[child_id] + 1

            metadata = cursor.fetchone()

    return by_study


def report_usage(email_address: typing.Optional[str],
        action_name: typing.Optional[str],
        args_snapshot: typing.Optional[str],
        cursor_maybe: OptionalCursor = None) -> None:
    """Record that a user took an action.

    @param email_address: The email address of the user.
    @param action_name: The name of the action taken.
    @param args_snapshot: Description of the arguments used in the action
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            'INSERT INTO usage_report VALUES (?, ?, ?, ?)',
            (
                'None' if email_address == None else email_address,
                'None' if action_name == None else action_name,
                'None' if args_snapshot == None else args_snapshot,
                datetime.datetime.now().isoformat()
            )
        )


def get_consent_settings(study: str,
        cursor_maybe: OptionalCursor = None) -> models.ConsentFormSettings:
    """Get the consent settings for a study.

    Get the consent settings for a study, returning a default if one not
    previously persisted.

    @param study: The name of the study.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @returns: The study consent settings or an unsaved record representing the
        default.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            SELECT
                study,
                requirement_type,
                form_content,
                other_options,
                epoch_updated
            FROM
                consent_settings
            ORDER BY
                epoch_updated DESC
            '''
        )

        prior_settings = cursor.fetchone()

    if prior_settings == None:
        return models.ConsentFormSettings(
            study,
            constants.CONSENT_FORM_NONE,
            '',
            [],
            None
        )
    else:
        epoch_updated = int(prior_settings[4])
        updated = datetime.datetime.utcfromtimestamp(epoch_updated)
        return models.ConsentFormSettings(
            prior_settings[0],
            int(prior_settings[1]),
            prior_settings[2],
            prior_settings[3].split('\n'),
            updated
        )


def put_consent_settings(consent_settings: models.ConsentFormSettings,
        cursor_maybe: OptionalCursor = None) -> None:
    """Save consent form settings to database.

    @param consent_settings: The consent settings to persist.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    values = (
        consent_settings.study,
        consent_settings.requirement_type,
        consent_settings.form_content,
        '\n'.join(consent_settings.other_options),
        int(time.time())
    )

    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            INSERT INTO
                consent_settings (
                    study,
                    requirement_type,
                    form_content,
                    other_options,
                    epoch_updated
                )
            VALUES
                (?, ?, ?, ?, ?)
            ''',
            values
        )


def get_consent_filings(study: str,
        cursor_maybe: OptionalCursor = None) -> typing.List[models.ConsentFormFiling]:
    """Get all of the filed consent forms for a study.

    @param study: The name of the stufy for which consent forms should be
        returned.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    @returns: List of consent forms filed for the given study.
    """
    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            SELECT
                study,
                name,
                child_id,
                completed,
                other_options,
                email,
                access_key
            FROM
                consent_filings
            WHERE
                study = ?
            ''',
            (study,)
        )

        results_raw = cursor.fetchall()

    def parse_record(record_raw):
        study = record_raw[0]
        name = record_raw[1]
        child_id = record_raw[2]
        other_options_list = record_raw[4].split('\n')
        email = record_raw[5]
        access_key = record_raw[6]

        completed_int = int(record_raw[3])
        completed = datetime.datetime.utcfromtimestamp(completed_int)

        return models.ConsentFormFiling(
            study,
            name,
            child_id,
            completed,
            other_options_list,
            email,
            access_key
        )

    results = map(parse_record, results_raw)

    return list(results)


def put_consent_filing(filing: models.ConsentFormFiling,
        cursor_maybe: OptionalCursor = None) -> None:
    """Persist a consent filing record.

    @param filing: The filing to save to the database.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    study = filing.study
    name = filing.name
    child_id = filing.child_id
    completed = int(filing.completed.timestamp())
    other_options = '\n'.join(filing.other_options)
    email = filing.email.lower().strip()
    access_key = filing.access_key

    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''
            INSERT INTO
                consent_filings (
                    study,
                    name,
                    child_id,
                    completed,
                    other_options,
                    email,
                    access_key
                )
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                study,
                name,
                child_id,
                completed,
                other_options,
                email,
                access_key
            )
        )


def delete_consent_filings(email: str,
        cursor_maybe: OptionalCursor = None) -> None:
    """Delete all consent forms filed for an email address.

    @param email: The email address for which records should be deleted.
    @param cursor_maybe: The cursor to use or None to get a new cursor.
    """
    email_clean = email.lower().strip()

    with get_realized_cursor(cursor_maybe) as cursor:
        cursor.execute(
            '''DELETE FROM consent_filings WHERE email = ?''',
            (email_clean,)
        )
