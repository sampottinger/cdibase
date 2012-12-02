class MCDIFormatMetadata:
    def __init__(self, human_name, safe_name, filename):
        self.human_name = human_name
        self.safe_name = safe_name
        self.filename = filename


class MCDIFormat(MCDIFormatMetadata):
    def __init__(self, human_name, safe_name, filename, details):
        MCDIFormatMetadata.__init__(self, human_name, safe_name, filename)
        self.details = details


class ValueMapping:
    def __init__(self):
        self.mapping = {}

    def add_mapping(self, orig_val, new_val):
        self.mapping[orig_val] = new_val


class PresentationFormatMetadata:
    def __init__(self, human_name, safe_name, filename):
        self.human_name = human_name
        self.safe_name = safe_name
        self.filename = filename


class PresentationFormat(PresentationFormatMetadata):
    def __init__(self, human_name, safe_name, filename, details):
        PresentationFormatMetadata.__init__(self, human_name, safe_name, filename)
        self.details = details


class PercentileTableMetadata:
    def __init__(self, human_name, safe_name, filename):
        self.human_name = human_name
        self.safe_name = safe_name
        self.filename = filename


class PercentileTable(PercentileTableMetadata):
    def __init__(self, human_name, safe_name, filename, details):
        PercentileTableMetadata.__init__(self, human_name, safe_name, filename)
        self.details = details


class SnapshotMetadata:
    def __init__(self, database_id, child_id, study_id, study, gender, age,
        birthday, session_date, session_num, total_num_sessions, words_spoken,
        items_excluded, percentile, extra_categories, revision, languages,
        num_languages, mcdi_type, hard_of_hearing):
        self.database_id = database_id
        self.child_id = child_id
        self.study_id = study_id
        self.study = study
        self.gender = gender
        self.age = age
        self.birthday = birthday
        self.session_date = session_date
        self.session_num = session_num
        self.total_num_sessions = total_num_sessions
        self.words_spoken = words_spoken
        self.items_excluded = items_excluded
        self.percentile = percentile
        self.extra_categories = extra_categories
        self.revision = revision
        self.languages = languages
        self.num_languages = num_languages
        self.mcdi_type = mcdi_type
        self.hard_of_hearing = hard_of_hearing


class SnapshotContent:
    def __init__(self, snapshot_id, word, value, revision):
        self.snapshot_id = snapshot_id
        self.word = word
        self.value = value
        self.revision = revision


class Filter:

    def __init__(self, field, operator, operand):
        self.field = field
        self.operator = operator
        self.operand = operand
        try:
            self.operand_float = float(self.operand)
        except ValueError:
            self.operand_float = None


class User:

    def __init__(self, email, password_hash, can_enter_data, can_access_data,
        can_change_formats, can_admin):
        self.email = email
        self.password_hash = password_hash
        self.can_enter_data = can_enter_data
        self.can_access_data = can_access_data
        self.can_change_formats = can_change_formats
        self.can_admin = can_admin
