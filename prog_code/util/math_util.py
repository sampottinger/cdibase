"""Misc. mathematical routines to suppor the application.

@author: Sam Pottinger
@license: GNU GPL v2
"""


def find_percentile(table_entries, target_num_words, age_months, max_words):
    """Find the MCDI perentile for a child.

    @param table_entries: The percentile table to use to calculate the
        child MCDI percentile.
    @type table_entries: 2D float array (list of list of numbers)
    @param target_num_words: The number of words reported as spoken by the
        child for which an MCDI percentile is desired.
    @type target_num_words: int
    @param age_months: The age of the child in months.
    @type age_months: int
    @param max_words: The number of words from the MCDI format that the child
        could know.
    @type max_words: int
    """
    percentiles = map(lambda x: int(x[0]), table_entries[1:])
    percentiles.insert(0,0)
    percentiles.append(0)

    first_month = int(table_entries[0][1])
    month_index = int(age_months - first_month + 1)

    words_per_percentile = map(lambda x: int(x[month_index]), table_entries)
    words_per_percentile.append(0)
    words_per_percentile[0] = max_words

    percentile_index = len(words_per_percentile) - 1
    cur_num_words = words_per_percentile[percentile_index]
    while target_num_words > cur_num_words:
        percentile_index -= 1
        cur_num_words = words_per_percentile[percentile_index]

    if percentile_index == 0:
        return percentiles[percentile_index]

    upper_section_words = cur_num_words
    lower_section_words = words_per_percentile[percentile_index+1]
    upper_section_percentile = percentiles[percentile_index]
    lower_section_percentile = percentiles[percentile_index+1]

    percentile_range = upper_section_percentile - lower_section_words
    word_range = upper_section_words - lower_section_words
    distance_from_lower = target_num_words - lower_section_words

    interpolation_slope = percentile_range / float(word_range)
    return interpolation_slope * distance_from_lower + lower_section_percentile