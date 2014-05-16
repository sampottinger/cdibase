"""Logic for building CSV reports and zip archives of CSV files.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import csv
import StringIO as string_io
import urllib
import zipfile

import constants
import db_util

PRESENTATION_VALUE_NAME_MAP = {
    constants.NO_DATA: 'no_data',
    constants.UNKNOWN: 'unknown',
    constants.POSSIBLY_WRONGLY_REC: 'possibly_wrongly_recorded',
    constants.EMERGENCY_REC: 'emergency',
    constants.IMPLIED_FALSE: 'implied_false',
    constants.IMPLIED_TRUE: 'implied_true',
    constants.EXPLICIT_TRUE: 'explicit_true',
    constants.EXPLICIT_FALSE: 'explicit_false',
    constants.EXPLICIT_NONE: 'explicit_none',
    constants.EXPLICIT_NA: 'explicit_na',
    constants.EXPLICIT_OTHER: 'explicit_other',
    constants.NO_EXTRA_CATEGORIES: 'no_extra_categories',
    constants.EXTRA_CATEGORIES: 'extra_categories',
    constants.MALE: 'male',
    constants.FEMALE: 'female',
    constants.OTHER_GENDER: 'other_gender',
    constants.ELEVEN_PRESUMED_TRUE: 'explicit_true'
}

DEFAULT_MCDI = 'fullenglishmcdi'


class NotFoundSnapshotContent:
    """A stand-in word snapshot content model.

    A word snapshot content model that represents that a word value is not
    available for a snapshot.
    """

    def __init__(self):
        """Create a new stand-in snapshot content model instance."""
        self.value = constants.NO_DATA


def interpret_word_value(value, presentation_format):
    """Convert underlying special database value to a string descriptions.

    @param value: The value to get a string description for.
    @type value: int
    @param presentation_format: Presentation format information to use to
        convert the value to a string description.
    @type presentation_format: models.PresentationFormat
    @return: Description of the value or the original value if it is not
        indiciated as being special in the given presentation_format.
    @rtype: str or original value type
    """
    try:
        value = int(value)
    except ValueError:
        pass

    name = PRESENTATION_VALUE_NAME_MAP.get(value, value)

    if presentation_format == None or not name in presentation_format.details:
        return value
    return presentation_format.details[name]


def serialize_snapshot(snapshot, presentation_format=None, word_listing=None,
    report_dict=False, include_words=True):
    """Turn a snapshot uft8 encoded list of strings.

    @param snapshot: The snapshot to serialize.
    @type snapshot: models.SnapshotMetadata
    @param presentation_format: The presentation format to use to render the
        string serialization.
    @type presentation_format: models.PresentationFormat
    @return: Serialized version of the snapshot.
    @rtype: List of str
    """
    if not word_listing:
        word_listing = []

    if include_words:
        snapshot_contents = db_util.load_snapshot_contents(snapshot)
        snapshot_contents_dict = {}

        for entry in snapshot_contents:
            snapshot_contents_dict[entry.word.lower().replace('*', '')] = entry

        not_found_entry = NotFoundSnapshotContent()
        snapshot_contents_sorted = map(
            lambda x: snapshot_contents_dict.get(x.lower().replace('*', ''), not_found_entry),
            word_listing
        )

        word_values = map(
            lambda x: interpret_word_value(x.value, presentation_format),
            snapshot_contents_sorted
        )

    if report_dict:
        gender = interpret_word_value(snapshot.gender, presentation_format)
        extra_categories = interpret_word_value(snapshot.extra_categories,
            presentation_format)
        return_dict = {
            'database_id': snapshot.database_id,
            'child_id': snapshot.child_id,
            'study_id': snapshot.study_id,
            'study': snapshot.study,
            'gender': gender,
            'age': snapshot.age,
            'birthday': snapshot.birthday,
            'session_date': snapshot.session_date,
            'session_num': snapshot.session_num,
            'total_num_sessions': snapshot.total_num_sessions,
            'words_spoken': snapshot.words_spoken,
            'items_excluded': snapshot.items_excluded,
            'percentile': snapshot.percentile,
            'extra_categories': extra_categories,
            'revision': snapshot.revision,
            'languages': snapshot.languages,
            'num_languages': snapshot.num_languages,
            'mcdi_type': snapshot.mcdi_type,
            'hard_of_hearing': snapshot.hard_of_hearing,
            'deleted': snapshot.deleted
        }

        if include_words:
            return_dict['words'] = word_values

        return return_dict

    else:
        return_list = [
            snapshot.database_id,
            snapshot.child_id,
            snapshot.study_id,
            snapshot.study,
            interpret_word_value(snapshot.gender, presentation_format),
            snapshot.age,
            snapshot.birthday,
            snapshot.session_date,
            snapshot.session_num,
            snapshot.total_num_sessions,
            snapshot.words_spoken,
            snapshot.items_excluded,
            snapshot.percentile,
            interpret_word_value(snapshot.extra_categories, presentation_format),
            snapshot.revision,
            snapshot.languages,
            snapshot.num_languages,
            snapshot.mcdi_type,
            snapshot.hard_of_hearing,
            snapshot.deleted
        ]

        if include_words:
            return_list.extend(word_values)

        return_list = map(
            lambda x: x.encode('utf-8','ignore') if isinstance(x, str) else x,
            return_list
        )

        return return_list


def generate_study_report_rows(snapshots_from_study, presentation_format):
    """Serialize a set of snapshots to a collection of lists of strings.

    @param snapshots_by_study: The snapshots to serialize.
    @type snapshots_by_study: Iterable of models.SnapshotMetadata
    @param presentation_format: The presentation format to use to render the
        string serialization.
    @type: presentation_format: models.PresentationFormat
    @return: List of serialized versions of snapshots with first list with
        header information.
    @rtype: List of list of str.
    """
    snapshot_contents = db_util.load_snapshot_contents(snapshots_from_study[0])
    word_listing = map(
        lambda x: x.word.encode('utf-8','ignore'),
        snapshot_contents
    )
    word_listing.sort()

    serialized_snapshots = map(
        lambda x: serialize_snapshot(x, presentation_format, word_listing),
        snapshots_from_study
    )
    
    header_col = [
        'database id',
        'child id',
        'study id',
        'study',
        'gender',
        'age',
        'birthday',
        'session date',
        'session num',
        'total num sessions',
        'words spoken',
        'items excluded',
        'percentile',
        'extra categories',
        'revision',
        'languages',
        'num languages',
        'mcdi type',
        'hard of hearing',
        'deleted'
    ]
    header_col.extend(word_listing)

    cols = [header_col]
    cols.extend(serialized_snapshots)

    return zip(*cols)


def sort_by_study_order(rows, mcdi_format):
    """Sort report output rows such that they are in the same order as the MCDI.

    Sort the reourt output rows such that the header rows come first followed
    by the word value rows in the same order as they appear in the original
    MCDI.

    @param rows: The rows to sort including both the 20 header rows and the 
        word value rows.
    @type rows: iterable over iterable over primitive
    @param mcdi_format: Information about the presentation format whose
        MCDI format should be sorted against.
    @type mcdi_format: models.MCDIFormat
    @return: Rows sorted acording to the presentation format.
    @rtype: iterable over iterable over primitive
    """
    categories = mcdi_format.details['categories']
    word_index = {}
    i = 0
    for category in categories:
        for word in category['words']:
            word_index[word.lower().replace('*', '')] = i
            i+=1

    rows_header = rows[:20]
    rows_content_indexed = map(
        lambda x: (word_index.get(x[0].lower().replace('*', ''), -1), x),
        rows[20:]
    )
    rows_content_sorted = sorted(rows_content_indexed, key=lambda x: x[0])
    rows_content_sorted = map(lambda x: x[1], rows_content_sorted)
    return rows_header + rows_content_sorted


def generate_study_report_csv(snapshots_from_study, presentation_format):
    """Generate a CSV file for a set of snapshots with the same MCDI format.

    @param snapshots_from_study: The snapshots to create a CSV report for.
    @type snapshots_from_study: Iterable over models.SnapshotMetadata
    @param presentation_format: The presentation format to use to render the
        string serialization.
    @type: presentation_format: models.PresentationFormat
    @return: Contents of the CSV file.
    @rtype: StringIO.StringIO
    """
    faux_file = string_io.StringIO()
    csv_writer = csv.writer(faux_file)
    mcdi_type_name = snapshots_from_study[0].mcdi_type
    safe_mcdi_name = mcdi_type_name.replace(' ', '')
    safe_mcdi_name = urllib.quote_plus(safe_mcdi_name).lower()
    mcdi_format = db_util.load_mcdi_model(safe_mcdi_name)
    if mcdi_format == None:
        mcdi_format = db_util.load_mcdi_model(DEFAULT_MCDI)
    rows = generate_study_report_rows(snapshots_from_study, presentation_format)
    rows = sort_by_study_order(rows, mcdi_format)
    csv_writer.writerows(
        [[unicode(val).encode('ascii', 'replace') for val in row] for row in rows]
    )
    return faux_file


def generate_consolidated_study_report(snapshots, presentation_format):
    """Generate a unified CSV file for a set of snapshots

    @param snapshots_from_study: The snapshots to create a CSV report for.
    @type snapshots_from_study: Iterable over models.SnapshotMetadata
    @param presentation_format: The presentation format to use to render the
        string serialization.
    @type: presentation_format: models.PresentationFormat
    @return: Contents of the zip archive file.
    @rtype: StringIO.StringIO
    """
    snapshots.sort(key=lambda x: '%s_%s' % (x.session_num, x.study_id))

    return generate_study_report_csv(
        snapshots,
        presentation_format
    )


def generate_study_report(snapshots, presentation_format):
    """Generate a zip archive for a set of snapshots

    Create a zip archive of CSV reports for a set of snapshots where each study
    gets an individual CSV file in the archive.

    @param snapshots_from_study: The snapshots to create a CSV report for.
    @type snapshots_from_study: Iterable over models.SnapshotMetadata
    @param presentation_format: The presentation format to use to render the
        string serialization.
    @type: presentation_format: models.PresentationFormat
    @return: Contents of the zip archive file.
    @rtype: StringIO.StringIO
    """
    snapshots.sort(key=lambda x: '%s_%s' % (x.session_num, x.study_id))

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
        faux_files['%s.csv' % study_name] = report

    faux_zip_file = string_io.StringIO()
    zip_file = zipfile.ZipFile(faux_zip_file, mode='w')
    for (filename, faux_file) in faux_files.items():
        zip_file.writestr(filename, faux_file.getvalue())

    return faux_zip_file
