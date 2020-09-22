"""Utility functions used in remote consent forms.

Copyright (C) 2020 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

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
"""

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util


def requires_consent_form(child_id: str, study: str, access_key: str) -> bool:
    """Determine if a user needs to fill out a consent form.

    @param child_id: The across-study datatbase ID for the child.
    @param study: The study for which a consent form may be required.
    @param access_key: The access key being utilized.
    @returns: True if the parent needs to fill out a consent form for the given
        study and False otherwise.
    """
    # Get the current consent settings
    consent_settings = db_util.get_consent_settings(study)

    # Look at non-conditional requirement
    if consent_settings.requirement_type == constants.CONSENT_FORM_NONE:
        return False

    # Handle conditional requirement
    filings = db_util.get_consent_filings(study)

    if consent_settings.requirement_type == constants.CONSENT_FORM_ALWAYS:
        access_keys = set(map(lambda x: x.access_key, filings))
        already_completed = access_key in access_keys
        return not already_completed
    else: # Handle CONSENT_FORM_ONCE
        child_ids = set(map(lambda x: x.child_id, filings))
        has_prior_in_study = child_id in child_ids
        return not has_prior_in_study
