"""Utility functions for managing parent accounts.

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

@author Sam Pottinger
@license GNU GPL v3
"""
import os
import re
import typing

import dateutil.parser as dateutil_parser

from ..struct import models

import prog_code.util.db_util as db_util
import prog_code.util.filter_util as filter_util
import prog_code.util.mail_util as mail_util
import prog_code.util.user_util as user_util

CDI_EMAIL_SUBJECT = 'CU Language Project'

CDI_EMAIL_TEMPLATE = None

URL_TEMPLATE = 'https://cdi.colorado.edu/base/parent_cdi/%s'
EMAIL_REGEX = re.compile('^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$',
    re.IGNORECASE)


class AttributeResolutionResolver:
    """State machine that fills in missing values in parent form records."""

    def __init__(self):
        """Create a new resolution resolver without a user to load from."""
        self.__target_user = None

    def is_valid_value(self, value: typing.Union[int, str, None, typing.List]) -> bool:
        """Determine if an attribute of a parent form is valid.

        @param value: The attribute value to check.
        @type value: obj
        @return: True if the attribute is "valid" and False otherwise.
        @rtype: bool
        """
        return value != None and value != ''

    def set_global_id(self, new_global_id: typing.Optional[str]) -> None:
        """Set the global ID of the child to load missing form values from.

        @param new_global_id: The global ID of the child to start loading form
            values from.
        """
        if not self.is_valid_value(new_global_id):
            return

        try:
            new_global_id_parsed = int(new_global_id) # type: ignore
        except ValueError:
            return

        child_id_filter = models.Filter('child_id', 'eq', new_global_id_parsed)
        results = filter_util.run_search_query([child_id_filter], 'snapshots')
        if len(results) == 0:
            return

        results.sort(key=lambda x: x.session_date, reverse=True)
        self.__target_user = results[0]

    def set_study_id(self, study: typing.Optional[str], study_id: typing.Optional[str]) -> None:
        """Set the child to load missing values from using study information.

        Set the child to load missing form values from by finding the reference
        child using a study id and study name.

        @param study: The name of the study to find the child in.
        @type study: str
        @param study_id: The id of the child within the study to use as a
            reference to load missing form values from.
        @type study_id: str
        """
        if not self.is_valid_value(study) or not self.is_valid_value(study_id):
            return

        study_realized: str = study # type: ignore
        study_id_realized: str = study_id # type: ignore

        study_filter = models.Filter('study', 'eq', study_realized)
        study_id_filter = models.Filter('study_id', 'eq', study_id_realized)
        results = filter_util.run_search_query([study_filter, study_id_filter],
            'snapshots')
        if len(results) == 0:
            return

        results.sort(key=lambda x: x.session_date, reverse=True)
        self.__target_user = results[0]

    def fill_field(self, current_value: typing.Union[str, int, None],
            field_name: str) -> typing.Union[int, str, None]:
        """Fill a parent form value from the reference child information.

        @param current_value: The current form field value.
        @type current_value: int or str
        @param field_name: The name of the filed that the provided value is for
            and that should be filled if the value is not currently valid.
        @type field_name: str
        @return: The value to use for the provided field.
        @rtype: int or str
        """
        if not self.is_valid_value(current_value):
            if self.__target_user == None:
                return None
            else:
                return getattr(self.__target_user, field_name)
        else:
            return current_value # type: ignore

    def fill_field_int(self, current_value: typing.Union[str, int, None],
            field_name: str) -> int:
        """Fill a parent form value from the reference child information.

        @param current_value: The current form field value.
        @type current_value: int or str
        @param field_name: The name of the filed that the provided value is for
            and that should be filled if the value is not currently valid.
        @type field_name: str
        @return: The value to use for the provided field.
        @rtype: int
        """
        return self.fill_field(current_value, field_name) # type: ignore

    def fill_field_str(self, current_value: typing.Union[str, int, None],
            field_name: str) -> str:
        """Fill a parent form value from the reference child information.

        @param current_value: The current form field value.
        @type current_value: int or str
        @param field_name: The name of the filed that the provided value is for
            and that should be filled if the value is not currently valid.
        @type field_name: str
        @return: The value to use for the provided field.
        @rtype: str
        """
        return self.fill_field(current_value, field_name) # type: ignore

    def fill_parent_form_defaults(self, parent_form: models.ParentForm) -> None:
        """Fill all of the missing form values for the provided form.

        Using the reference child set eariler on this state machine, set all of
        the missing form value for the provided form.

        @param parent_form: The form to fill.
        @type parent_form: models.ParentForm
        """
        self.set_global_id(parent_form.database_id)
        self.set_study_id(parent_form.study, parent_form.study_id)

        parent_form.database_id = self.fill_field_str(
            parent_form.database_id,
            'child_id'
        )

        parent_form.study = self.fill_field_str(
            parent_form.study,
            'study'
        )

        parent_form.study_id = self.fill_field_str(
            parent_form.study_id,
            'study_id'
        )

        parent_form.gender = self.fill_field_int(
            parent_form.gender,
            'gender'
        )

        parent_form.birthday = self.fill_field_str(
            parent_form.birthday,
            'birthday'
        )

        parent_form.items_excluded = self.fill_field_int(
            parent_form.items_excluded,
            'items_excluded'
        )

        parent_form.extra_categories = self.fill_field_int(
            parent_form.extra_categories,
            'extra_categories'
        )

        parent_form.total_num_sessions = self.fill_field_int(
            parent_form.total_num_sessions,
            'total_num_sessions'
        )

        languages_valid = self.is_valid_value(parent_form.languages)
        if not languages_valid and self.__target_user != None:
            parent_form.languages = self.__target_user.languages
            parent_form.num_languages = self.__target_user.num_languages

        parent_form.hard_of_hearing = self.fill_field_int(
            parent_form.hard_of_hearing,
            'hard_of_hearing'
        )


def is_likely_email_address(target: str) -> bool:
    """Determine if the provided string is likely an email address.

    @param target: The string to test for containing an email address.
    @type target: str
    @return: True if the provided string likely contains an email address.
    @rtype: bool
    """
    return EMAIL_REGEX.match(target) != None


def generate_unique_cdi_form_id() -> str:
    """Generate a unique random parent CDI form ID.

    Generate a new parent CDI form ID that is not currently in use by other
    CDI forms and is unpredictable given previous IDs.

    @return: The newly generated form ID.
    @rtype: str
    """
    found = False
    ret_id = None
    while not found:
        ret_id = user_util.generate_password().lower()
        found = db_util.get_parent_form_by_id(ret_id) == None

    return ret_id # type: ignore


def get_cdi_email_template() -> str:
    """Load the CDI email template from disk.

    @returns: String contents of the CDI email template.
    """
    util_dir = os.path.dirname(os.path.realpath(__file__))
    prog_code_dir = os.path.dirname(util_dir)
    root_dir = os.path.dirname(prog_code_dir)
    taget_path = os.path.join(
        root_dir,
        'templates',
        'cdi_email_template.txt'
    )
    with open(taget_path) as f:
        content = f.read()

    return content


def send_cdi_email(parent_form: models.ParentForm) -> None:
    """Send an email with parent CDI form information.

    Sends an email to a parent with a link that the parent can follow to fill
    out an CDI form for thier child.

    @param parent_form: The form to send an email for.
    @type parent_form: models.ParentForm
    """
    form_url = URL_TEMPLATE % parent_form.form_id
    mail_util.send_msg(
        parent_form.parent_email,
        CDI_EMAIL_SUBJECT,
        get_cdi_email_template() % (parent_form.child_name, form_url)
    )


def get_snapshot_chronology_for_db_id(
        db_id: str) -> typing.List[models.SnapshotMetadata]:
    """Get snapshots for a child sorted in reverse chronological order.

    Get snapshots for a child sorted in reverse choronological order given the
    database ID of that child.

    @param db_id: The database ID of the child to get the snapshot chronology
        for.
    @type db_id: str
    @return: List of snapshots.
    @rtype: List of models.SnapshotMetadata
    """
    child_id_filter = models.Filter(
        'child_id',
        'eq',
        db_id
    )
    results = filter_util.run_search_query([child_id_filter], 'snapshots')
    results.sort(key=lambda x: x.session_date, reverse=True)
    return results

def get_snapshot_chronology_for_study_id(study: str,
        study_id: str) -> typing.List[models.SnapshotMetadata]:
    """Get the snapshots for a child sorted in reverse chronological order.

    Get the snapshots for a child sorted in reverse chronological order given
    the study / study ID of that child.

    @param study: The name of the study to find the child in.
    @type study: str
    @param study_id: The ID of the child within the study.
    @type study_id: str
    @return: List of snapshots.
    @rtype: List of models.SnapshotMetadata
    """
    study_filter = models.Filter(
        'study',
        'eq',
        study
    )
    id_filter = models.Filter(
        'study_id',
        'eq',
        study_id
    )
    results = filter_util.run_search_query(
        [study_filter, id_filter],
        'snapshots'
    )
    results.sort(key=lambda x: x.session_date, reverse=True)
    return results

def is_birthday_valid(birthday_maybe: typing.Optional[str]) -> bool:
    """Determine if the provided string description of a birthday is valid.

    Determine if the provided string does contain a valid date that can be
    parsed by the application.

    @param birthday_maybe: The string serialization of a date to test for
        parse-ability.
    @type birthday_maybe: str
    @return: True if the provided string can be parsed as a date. False
        otherwise.
    """
    if birthday_maybe == None:
        return False

    birthday: str = birthday_maybe # type: ignore
    try:
        dateutil_parser.parse(birthday, dayfirst=False, yearfirst=False)
        return True
    except ValueError:
        return False
