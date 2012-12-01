import db_util
import models

FIELD_MAP = {
    "child_id": "child_id",
    "study_id": "study_id",
    "study": "study",
    "gender": "gender",
    "birthday": "birthday",
    "session_date": "session_date",
    "session_num": "session_num",
    "words_spoken": "words_spoken",
    "items_excluded": "items_excluded",
    "age": "age",
    "total_num_sessions": "total_num_sessions",
    "percentile": "percentile",
    "extra_categories": "extra_categories",
    "MCDI_type": "mcdi_type",
    "specific_language": "languages",
    "num_languages": "num_languages",
    "hard_of_hearing": "hard_of_hearing"
}

OPERATOR_MAP = {
    "eq": "==",
    "lt": "<",
    "gt": ">",
    "neq": "!=",
    "lteg": "<=",
    "gteg": ">="
}


def build_search_query(filters, table):
    filter_fields = map(lambda x: x.field, filters)
    # TODO: might want to catch this as a security exception
    fitler_fields = filter(lambda x: x in FIELD_MAP, filter_fields)
    filter_fields = map(lambda x: FIELD_MAP[x], filter_fields)

    operators = map(lambda x: x.operator, filters)
    operators = filter(lambda x: x in OPERATOR_MAP, operators)
    operators = map(lambda x: OPERATOR_MAP[x], operators)

    fields_and_operators = zip(fitler_fields, operators)

    filter_fields_str = map(
        lambda (field, op): "%s %s ?" % (field, op), 
        fields_and_operators
    )
    clause = " AND ".join(filter_fields_str)

    return "SELECT * FROM %s WHERE %s" % (table, clause)

def run_search_query(filters, table):
    db_connection = db_util.get_db_connection()
    db_cursor = db_connection.cursor()

    query = build_search_query(filters, table)
    operands = map(lambda x: x.operand, filters)
    db_cursor.execute(query, operands)

    return map(lambda x: models.SnapshotMetadata(*x), db_cursor.fetchall())
