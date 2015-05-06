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

import constants
import db_util
import interp_util
import math_util


class CachedMCDIAdapter:

    def __init__(self):
        self.percentiles = {}
        self.mcdi_models = {}
        self.max_word_counts = {}

    def read_cdi_format_model(self, type_name):
        if type_name in self.mcdi_models:
            return self.mcdi_models[type_name]

        mcdi_model = db_util.read_cdi_format_model(type_name)
        self.mcdi_models[type_name] = mcdi_model
        return mcdi_model

    def read_percentile_model(self, type_name):
        if type_name in self.percentiles:
            return self.percentiles[type_name]

        percentile_model = db_util.read_percentile_model(type_name)
        self.percentiles[type_name] = percentile_model
        return percentile_model

    def get_max_mcdi_words(self, type_name):
        if type_name in self.max_word_counts:
            return self.max_word_counts[type_name]

        words = 0
        mcdi_model = self.read_cdi_format_model(type_name)
        if mcdi_model == None:
            mcdi_model = self.read_cdi_format_model('fullenglishmcdi')

        categories = mcdi_model.details['categories']
        category_num_words = map(lambda x: len(x['words']), categories)
        total_words = sum(category_num_words)
        self.max_word_counts[type_name] = total_words
        return total_words


def recalculate_age(snapshot):
    """
    @type snapshot: SnapshotMetadata
    """
    birthday = interp_util.interpret_date(snapshot.birthday)
    session_date = interp_util.interpret_date(snapshot.session_date)
    snapshot.age = interp_util.monthdelta(birthday, session_date)


def recalculate_percentile(snapshot, cached_adapter):
    """
    @type snapshot: SnapshotMetadata
    """
    mcdi_model = cached_adapter.read_cdi_format_model(snapshot.mcdi_type)
    if mcdi_model == None:
        mcdi_model = cached_adapter.read_cdi_format_model('fullenglishmcdi')

    meta_percentile_info = mcdi_model.details['percentiles']
    gender = snapshot.gender

    percentiles_name = None
    if gender == constants.MALE or gender == constants.OTHER_GENDER:
        percentiles_name = meta_percentile_info['male']
    else:
        percentiles_name = meta_percentile_info['female']

    percentiles = cached_adapter.read_percentile_model(percentiles_name)

    count_as_spoken_vals = mcdi_model.details['count_as_spoken']
    individual_words = db_util.load_snapshot_contents(snapshot)
    words_spoken = 0
    for word in individual_words:
        if word.value in count_as_spoken_vals:
            words_spoken += 1

    snapshot.words_spoken = words_spoken
    
    new_percentile = math_util.find_percentile(
        percentiles.details,
        snapshot.words_spoken,
        snapshot.age,
        cached_adapter.get_max_mcdi_words(snapshot.mcdi_type)
    )

    snapshot.percentile = new_percentile


def recalculate_ages(snapshots):
    for snapshot in snapshots:
        recalculate_age(snapshot)


def recalculate_percentiles(snapshots):
    adapter = CachedMCDIAdapter()
    for snapshot in snapshots:
        recalculate_percentile(snapshot, adapter)


def update_snapshot_models(snapshots):
    connection = db_util.get_db_connection()
    cursor = connection.cursor()

    for snapshot in snapshots:
        db_util.update_snapshot_model(snapshot, cursor)

    connection.commit()
    connection.close()


def recalculate_ages_and_percentiles(snapshots, save=True):
    recalculate_ages(snapshots)
    recalculate_percentiles(snapshots)

    if save:
        update_snapshot_models(snapshots)
