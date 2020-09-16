"""Misc. mathematical routines to support the application.

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
import typing


def get_mapped_with_end_max(collection: typing.List, index: int,
        mapping: typing.Mapping[str, int]) -> int:
    """Get the value at index or the last value in the colleciton.

    Get a value from collection if index is in range or the final value if the
    index is out of range.

    @param collection: The collection to get the value from.
    @param index: The index at which to get the value.
    @return: The target value.
    """
    if index >= len(collection):
        ret_val = collection[-1]
    else:
        ret_val = collection[index]

    if ret_val in mapping:
        return mapping[ret_val]

    return int(ret_val)


def find_percentile(table_entries: typing.List[typing.List[float]],
        target_num_words: int, age_months: float, max_words: int) -> float:
    """Find the CDI perentile for a child.

    @param table_entries: The percentile table to use to calculate the
        child CDI percentile.
    @type table_entries: 2D float array (list of list of numbers)
    @param target_num_words: The number of words reported as spoken by the
        child for which an CDI percentile is desired.
    @type target_num_words: int
    @param age_months: The age of the child in months.
    @type age_months: int
    @param max_words: The number of words from the CDI format that the child
        could know.
    @type max_words: int
    """
    percentiles = list(map(lambda x: int(x[0]), table_entries[1:]))
    percentiles.insert(0,0)
    percentiles.append(0)

    first_month = int(table_entries[0][1])
    month_index = int(age_months - first_month + 1)

    words_per_percentile = list(map(lambda x:
        get_mapped_with_end_max(x, month_index, {'%': 0}),
        table_entries
    ))
    words_per_percentile.append(0)
    words_per_percentile[0] = max_words

    percentile_index = len(words_per_percentile) - 1
    cur_num_words = words_per_percentile[percentile_index]
    while target_num_words > cur_num_words:
        percentile_index -= 1
        cur_num_words = words_per_percentile[percentile_index]

    if percentile_index == 0:
        return 99

    upper_section_words = cur_num_words
    if len(words_per_percentile) > percentile_index+1:
        lower_section_words = words_per_percentile[percentile_index+1]
    else:
        lower_section_words = upper_section_words - 1

    upper_section_percentile = percentiles[percentile_index]
    if len(percentiles) > percentile_index+1:
        lower_section_percentile = percentiles[percentile_index+1]
    else:
        lower_section_percentile = upper_section_percentile - 1

    percentile_range = upper_section_percentile - lower_section_percentile
    word_range = upper_section_words - lower_section_words
    distance_from_lower = target_num_words - lower_section_words

    interpolation_slope = percentile_range / float(word_range)
    return interpolation_slope * distance_from_lower + lower_section_percentile
