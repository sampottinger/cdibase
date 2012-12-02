def find_percentile(table_entries, target_num_words, age_months, max_words):
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