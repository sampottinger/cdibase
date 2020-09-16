"""Utility for recalculating values already in the lab database.

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
import typing

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util
import prog_code.util.filter_util as filter_util
import prog_code.util.interp_util as interp_util
import prog_code.util.math_util as math_util

from ..struct import models


DEFAULT_CDI = 'fullenglishcdi'


def get_cdi_model_by_name_or_default(
        adapter: 'CachedCDIAdapter',
        model_name: str,
        default_cdi: str = DEFAULT_CDI) -> models.CDIFormat:
    """Try getting a CDI format by name or use a default if not found.

    @param adapter: The adapter to use to query for the model.
    @param model_maybe: The model to test to see if None.
    @param default_cdi: The name of the model to use if model_maybe is None.
    """
    cdi_model = adapter.load_cdi_model(model_name)
    return realize_cdi_model(adapter, cdi_model)


def realize_cdi_model(
        adapter: 'CachedCDIAdapter',
        model_maybe: typing.Optional[models.CDIFormat],
        default_cdi: str = DEFAULT_CDI) -> models.CDIFormat:
    """If the given model is None, use a default.

    @param adapter: The adapter to use to query for the model.
    @param model_maybe: The model to test to see if None.
    @param default_cdi: The name of the model to use if model_maybe is None.
    """
    if model_maybe == None:
        model_maybe = adapter.load_cdi_model(DEFAULT_CDI)

    assert model_maybe != None
    return model_maybe # type: ignore


class CachedCDIAdapter:
    """Adapter around db_util that caches CDI information."""

    def __init__(self):
        """Create an empty adapter."""
        self.percentiles = {}
        self.cdi_models = {}
        self.max_word_counts = {}

    def load_cdi_model(self,
            type_name: str) -> typing.Optional[models.CDIFormat]:
        """See db_util.load_cdi_model"""
        if type_name in self.cdi_models:
            return self.cdi_models[type_name]

        cdi_model = db_util.load_cdi_model(type_name)
        self.cdi_models[type_name] = cdi_model
        return cdi_model

    def load_percentile_model(self,
            type_name: str) -> typing.Optional[models.PercentileTable]:
        """See db_util.load_percentile_model"""
        if type_name in self.percentiles:
            return self.percentiles[type_name]

        percentile_model = db_util.load_percentile_model(type_name)
        self.percentiles[type_name] = percentile_model
        return percentile_model

    def get_max_cdi_words(self, type_name: str) -> int:
        """Get the maximum number of words seen across all CDIs.

        @param type_name: The type of CDI.
        @returns: The maximum observed number of words.
        """
        if type_name in self.max_word_counts:
            return self.max_word_counts[type_name]

        words = 0
        cdi_model_realized = get_cdi_model_by_name_or_default(self, type_name)

        categories = cdi_model_realized.details['categories']
        category_num_words = map(lambda x: len(x['words']), categories)
        total_words = sum(category_num_words)
        self.max_word_counts[type_name] = total_words
        return total_words


def recalculate_age(snapshot: models.SnapshotMetadata) -> None:
    """Recalculate the age for a snapshot to be modified in place.

    @param snapshot: The snapshot to modify.
    """
    snapshot.age = recalculate_age_raw(snapshot.birthday, snapshot.session_date)


def recalculate_age_raw(birthday_str: str, session_date_str: str) -> float:
    """Recalculate the age for a snapshot.

    @param birthday_str: The birthday of the participant.
    @param session_date_str: Date of the session.
    @returns: Age in amoritized months.
    """
    birthday = interp_util.interpret_date(birthday_str)
    session_date = interp_util.interpret_date(session_date_str)
    return interp_util.monthdelta(birthday, session_date)


def recalculate_percentile(snapshot: models.SnapshotMetadata,
        cached_adapter: CachedCDIAdapter) -> None:
    """Recalculate the percentile for a snapshot to be modified in place.

    @param snapshot: The snapshot to modify.
    """
    cdi_type = snapshot.cdi_type
    gender = snapshot.gender
    individual_words = db_util.load_snapshot_contents(snapshot)

    snapshot.words_spoken = get_words_spoken(
        cached_adapter,
        cdi_type,
        individual_words
    )

    snapshot.percentile = recalculate_percentile_raw(
        cached_adapter,
        cdi_type,
        gender,
        snapshot.words_spoken,
        snapshot.age
    )


def recalculate_percentile_raw(cached_adapter: CachedCDIAdapter, cdi_type: str,
        gender: int, words_spoken: int, age: float) -> float:
    """Recalculate the percentile for a snapshot.

    @param cached_adapter: Adapter to get CDI information.
    @param cdi_type: The type of CDI in which the percentile is being
        calculated.
    @param gender: The gender of the participant.
    @param words_spoken: Number of words spoken in snapshot.
    @param age: Participant age in months at time of snapshot.
    @returns: Newly calculated percentile.
    """
    # Load CDI information
    cdi_model = cached_adapter.load_cdi_model(cdi_type)
    if cdi_model == None:
        cdi_model = cached_adapter.load_cdi_model('fullenglishcdi')

    # Get percentile information
    meta_percentile_info = cdi_model.details['percentiles']

    percentiles_name = None
    if gender == constants.MALE or gender == constants.OTHER_GENDER:
        percentiles_name = meta_percentile_info['male']
    else:
        percentiles_name = meta_percentile_info['female']

    percentiles = cached_adapter.load_percentile_model(percentiles_name)

    # Calculate percentile
    return math_util.find_percentile(
        percentiles.details,
        words_spoken,
        age,
        cached_adapter.get_max_cdi_words(cdi_type)
    )

def get_words_spoken(cached_adapter, cdi_type, individual_words):
    cdi_model = cached_adapter.load_cdi_model(cdi_type)
    if cdi_model == None:
        cdi_model = cached_adapter.load_cdi_model('fullenglishcdi')

    count_as_spoken_vals = cdi_model.details['count_as_spoken']

    words_spoken = 0
    for word in individual_words:
        if word.value in count_as_spoken_vals:
            words_spoken += 1

    return words_spoken

def recalculate_ages(snapshots):
    for snapshot in snapshots:
        recalculate_age(snapshot)


def recalculate_percentiles(snapshots):
    adapter = CachedCDIAdapter()
    for snapshot in snapshots:
        recalculate_percentile(snapshot, adapter)


def update_snapshots(snapshots):
    connection = db_util.get_db_connection()
    cursor = connection.cursor()

    for snapshot in snapshots:
        db_util.update_snapshot(snapshot, cursor)

    connection.commit()
    connection.close()


def recalculate_ages_and_percentiles(snapshots, save=True):
    recalculate_ages(snapshots)
    recalculate_percentiles(snapshots)

    if save:
        update_snapshots(snapshots)


def get_session_number(study, study_id):
    study_filter = models.Filter('study', 'eq', study)
    study_id_filter = models.Filter('study_id', 'eq', study_id)
    results = filter_util.run_search_query([study_filter, study_id_filter],
        'snapshots')
    return len(results) + 1
