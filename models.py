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


class Filter:

    def __init__(self, field, operator, operand):
        self.field = field
        self.operator = operator
        self.operand = operand
        try:
            self.operand_float = float(self.operand)
        except ValueError:
            self.operand_float = None
