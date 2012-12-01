import csv
import StringIO as string_io
import zipfile

import constants
import db_util

PRESENTATION_VALUE_NAME_MAP = {
    constants.NO_DATA: "no_data",
    constants.UNKNOWN: "unknown",
    constants.POSSIBLY_WRONGLY_REC: "possibly_wrongly_recorded",
    constants.EMERGENCY_REC: "emergency",
    constants.IMPLIED_FALSE: "implied_false",
    constants.EXPLICIT_TRUE: "explicit_true",
    constants.EXPLICIT_FALSE: "explicit_false",
    constants.EXPLICIT_NONE: "explicit_none",
    constants.EXPLICIT_NA: "explicit_na",
    constants.EXPLICIT_OTHER: "explicit_other",
    constants.NO_EXTRA_CATEGORIES: "no_extra_categories",
    constants.EXTRA_CATEGORIES: "extra_categories",
    constants.MALE: "male",
    constants.FEMALE: "female",
    constants.OTHER_GENDER: "other_gender"
}

def interpret_word_value(value, presentation_format):
    if not value in PRESENTATION_VALUE_NAME_MAP:
        return value
    name = PRESENTATION_VALUE_NAME_MAP[value]

    if not name in presentation_format.details:
        return value
    return presentation_format.details[name]


def serialize_snapshot(snapshot, presentation_format):
    target_buffer = string_io.StringIO()
    snapshot_contents = db_util.load_snapshot_contents(snapshot)
    snapshot_contents.sort(key=lambda x: x.word)

    return_list = [
        snapshot.database_id,
        snapshot.child_id,
        snapshot.study_id,
        snapshot.study,
        snapshot.gender,
        snapshot.age,
        snapshot.birthday,
        snapshot.session_date,
        snapshot.session_num,
        snapshot.total_num_sessions,
        snapshot.words_spoken,
        snapshot.items_excluded,
        snapshot.percentile,
        snapshot.extra_categories,
        snapshot.revision,
        snapshot.languages,
        snapshot.num_languages,
        snapshot.mcdi_type,
        snapshot.hard_of_hearing
    ]

    word_values = map(
        lambda x: interpret_word_value(x.value, presentation_format),
        snapshot_contents
    )
    return_list.extend(word_values)

    return_list = map(
        lambda x: x.encode("utf-8","ignore") if isinstance(x, str) else x,
        return_list
    )

    return return_list

def generate_study_report_rows(snapshots_from_study, presentation_format):

    snapshot_contents = db_util.load_snapshot_contents(snapshots_from_study[0])
    word_listing = map(
        lambda x: x.word.encode("utf-8","ignore"),
        snapshot_contents
    )
    word_listing.sort()

    serialized_snapshots = map(
        lambda x: serialize_snapshot(x, presentation_format),
        snapshots_from_study
    )
    
    header_col = [
        "database id",
        "child id",
        "study id",
        "study",
        "gender",
        "age",
        "birthday",
        "session date",
        "session num",
        "total num sessions",
        "words spoken",
        "items excluded",
        "percentile",
        "extra categories",
        "revision",
        "languages",
        "num languages",
        "mcdi type",
        "hard of hearing"
    ]
    header_col.extend(word_listing)

    cols = [header_col]
    cols.extend(serialized_snapshots)

    return zip(*cols)

def generate_study_report_csv(snapshots_from_study, presentation_format):
    faux_file = string_io.StringIO()
    csv_writer = csv.writer(faux_file)
    csv_writer.writerows(
        generate_study_report_rows(snapshots_from_study, presentation_format))
    return faux_file

def generate_study_report(snapshots, presentation_format):
    snapshots_by_study = {}
    for snapshot in snapshots:
        study = snapshot.study
        if not study in snapshots_by_study:
            snapshots_by_study[study] = []
        snapshots_by_study[study].append(snapshot)

    faux_files = {}
    for study_name in sorted(snapshots_by_study.keys()):
        report = generate_study_report_csv(
            snapshots_by_study[study_name],
            presentation_format
        )
        faux_files["%s.csv" % study_name] = report

    faux_zip_file = string_io.StringIO()
    zip_file = zipfile.ZipFile(faux_zip_file, mode="w")
    for (filename, faux_file) in faux_files.items():
        zip_file.writestr(filename, faux_file.getvalue())

    return faux_zip_file
