"""Logic for managing user-generated database queries.

@author: Sam Pottinger
@license: GNU GPL v2
"""

from ..struct import models

import db_util

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
    """Build a string SQL query from the given filters.

    @param filters: The filters to build the query out of.
    @type filters: Iterable over models.Filter
    @param table: The name of the table to query.
    @type table: str
    @return: SQL select query for the given table with the given filters.
    @rtype: str
    """
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
    """Builds and runs a SQL select query on the given table with given filters.

    @param filters: The filters to build the query out of.
    @type: Iterable over models.Filter
    @param table: The name of the table to query.
    @type table: str
    @return: Results of SQL select query for the given table with the given
        filters.
    @rtype: Iterable over models.SnapshotMetadata
    """
    db_connection = db_util.get_db_connection()
    db_cursor = db_connection.cursor()

    query = build_search_query(filters, table)
    operands = map(lambda x: x.operand, filters)
    db_cursor.execute(query, operands)

    ret_val = map(lambda x: models.SnapshotMetadata(*x), db_cursor.fetchall())
    db_connection.close()
    return ret_val
