"""Logic for managing user-generated database queries.

@author: Sam Pottinger
@license: GNU GPL v2
"""

from ..struct import models

import constants
import db_util
import oper_interp


FIELD_MAP = {
    "child_id": oper_interp.RawInterpretField("child_id"),
    "study_id": oper_interp.RawInterpretField("study_id"),
    "study": oper_interp.RawInterpretField("study"),
    "gender": oper_interp.GenderField("gender"),
    "birthday": oper_interp.RawInterpretField("birthday"),
    "session_date": oper_interp.RawInterpretField("session_date"),
    "session_num": oper_interp.NumericalField("session_num"),
    "words_spoken": oper_interp.NumericalField("words_spoken"),
    "items_excluded": oper_interp.NumericalField("items_excluded"),
    "age": oper_interp.NumericalField("age"),
    "total_num_sessions": oper_interp.NumericalField("total_num_sessions"),
    "percentile": oper_interp.NumericalField("percentile"),
    "extra_categories": oper_interp.NumericalField("extra_categories"),
    "MCDI_type": oper_interp.RawInterpretField("mcdi_type"),
    "specific_language": oper_interp.RawInterpretField("languages"),
    "num_languages": oper_interp.NumericalField("num_languages"),
    "hard_of_hearing": oper_interp.BooleanField("hard_of_hearing")
}

OPERATOR_MAP = {
    "eq": "==",
    "lt": "<",
    "gt": ">",
    "neq": "!=",
    "lteq": "<=",
    "gteq": ">="
}


class QueryInfo:
    """Information necessary to execute a user generated SQL select."""

    def __init__(self, filter_fields, query_str):
        """Create a structure containing info needed to run SQL select.

        @param filter_fields: The filters that are included in this select
            query.
        @type filter_fields: Iterable over oper.interp.FieldInfo
        @param query_str: SQL select statement with placeholders for operand
            values.
        @type query_str: str
        """
        self.filter_fields = filter_fields
        self.query_str = query_str


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
    filter_fields = filter(lambda x: x in FIELD_MAP, filter_fields)
    filter_fields = map(lambda x: FIELD_MAP[x], filter_fields)

    operators = map(lambda x: x.operator, filters)
    operators = map(lambda x: x.encode("utf8"), operators)
    operators = filter(lambda x: x in OPERATOR_MAP, operators)
    operators = map(lambda x: OPERATOR_MAP[x], operators)

    fields_and_operators = zip(filter_fields, operators)

    filter_fields_str = map(
        lambda (field, op): "%s %s ?" % (field.get_field_name(), op), 
        fields_and_operators
    )
    clause = " AND ".join(filter_fields_str)

    stmt = "SELECT * FROM %s WHERE %s" % (table, clause)

    return QueryInfo(filter_fields, stmt)

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

    query_info = build_search_query(filters, table)
    raw_operands = map(lambda x: x.operand, filters)
    filter_fields_and_operands = zip(query_info.filter_fields, raw_operands)
    operands = map(
        lambda (field, operand): field.interpret_value(operand),
        filter_fields_and_operands
    )
    db_cursor.execute(query_info.query_str, operands)

    ret_val = map(lambda x: models.SnapshotMetadata(*x), db_cursor.fetchall())
    db_connection.close()
    return ret_val
