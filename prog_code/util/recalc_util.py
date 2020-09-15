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

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util
import prog_code.util.filter_util as filter_util
import prog_code.util.interp_util as interp_util
import prog_code.util.math_util as math_util

from ..struct import models


class CachedCDIAdapter:

    def __init__(self):
        self.percentiles = {}
        self.cdi_models = {}
        self.max_word_counts = {}

    def load_cdi_model(self, type_name):
        if type_name in self.cdi_models:
            return self.cdi_models[type_name]

        cdi_model = db_util.load_cdi_model(type_name)
        self.cdi_models[type_name] = cdi_model
        return cdi_model

    def load_percentile_model(self, type_name):
        if type_name in self.percentiles:
            return self.percentiles[type_name]

        percentile_model = db_util.load_percentile_model(type_name)
        self.percentiles[type_name] = percentile_model
        return percentile_model

    def get_max_cdi_words(self, type_name):
        if type_name in self.max_word_counts:
            return self.max_word_counts[type_name]

        words = 0
        cdi_model = self.load_cdi_model(type_name)
        if cdi_model == None:
            cdi_model = self.load_cdi_model('fullenglishcdi')

        categories = cdi_model.details['categories']
        category_num_words = map(lambda x: len(x['words']), categories)
        total_words = sum(category_num_words)
        self.max_word_counts[type_name] = total_words
        return total_words


def recalculate_age(snapshot):
    """
    @type snapshot: SnapshotMetadata
    """
    snapshot.age = recalculate_age_raw(snapshot.birthday, snapshot.session_date)


def recalculate_age_raw(birthday_str, session_date_str):
    birthday = interp_util.interpret_date(birthday_str)
    session_date = interp_util.interpret_date(session_date_str)
    return interp_util.monthdelta(birthday, session_date)


def recalculate_percentile(snapshot, cached_adapter):
    """
    @type snapshot: SnapshotMetadata
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


def recalculate_percentile_raw(cached_adapter, cdi_type, gender,
    words_spoken, age):

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
