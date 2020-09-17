"""Logic for managing user-generated database queries.

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
import numbers
import typing

from ..struct import models

import prog_code.util.constants as constants
import prog_code.util.db_util as db_util
import prog_code.util.oper_interp as oper_interp


FIELD_MAP: typing.Mapping[str, oper_interp.FieldInfo] = {
    'child_id': oper_interp.RawInterpretField('child_id'),
    'study_id': oper_interp.RawInterpretField('study_id'),
    'study': oper_interp.RawInterpretField('study'),
    'gender': oper_interp.GenderField('gender'),
    'birthday': oper_interp.DateInterpretField('birthday'),
    'session_date': oper_interp.DateInterpretField('session_date'),
    'session_num': oper_interp.NumericalField('session_num'),
    'words_spoken': oper_interp.NumericalField('words_spoken'),
    'items_excluded': oper_interp.NumericalField('items_excluded'),
    'age': oper_interp.NumericalField('age'),
    'total_num_sessions': oper_interp.NumericalField('total_num_sessions'),
    'percentile': oper_interp.NumericalField('percentile'),
    'extra_categories': oper_interp.NumericalField('extra_categories'),
    'CDI_type': oper_interp.RawInterpretField('cdi_type'),
    'specific_language': oper_interp.RawInterpretField('languages'),
    'num_languages': oper_interp.NumericalField('num_languages'),
    'hard_of_hearing': oper_interp.BooleanField('hard_of_hearing'),
    'deleted': oper_interp.BooleanField('deleted')
}

OPERATOR_MAP = {
    'eq': '==',
    'lt': '<',
    'gt': '>',
    'neq': '!=',
    'lteq': '<=',
    'gteq': '>='
}


class QueryInfo:
    """Information necessary to execute a user generated SQL select."""

    def __init__(self, filter_fields: typing.List[oper_interp.FieldInfo],
            query_str:str):
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


def build_query_component(field: oper_interp.FieldInfo, operator: str,
        operand: str) -> str:
    """Generate part of a query for SQL.

    Generate part of a query for SQL without checking for security issues,
    issues which can be found through build_query.

    @param field: The field to query.
    @param operator: The operator to use in comparison.
    @param operand: The value to compare against.
    @returns: Query component.
    """
    if isinstance(operand, str):
        operands = operand.split(',')
    else:
        operands = [operand]
    query_subcomponents = []
    for operand in operands:
        template_vals = (field.get_field_name(), operator)
        query_subcomponents.append('%s %s ?' % template_vals)

    if len(operands) > 0:
        return '(' + ' OR '.join(query_subcomponents) + ')'
    else:
        return query_subcomponents[0]


def build_query(filters: typing.Iterable[models.Filter], table: str,
        statement_template: str) -> QueryInfo:
    """Build a SQL query to look up existing data.

    @param filters: The filters to apply within the query.
    @param table: The name of the table to query.
    @param statement_template: SQL template to fill in.
    """
    filters_realized = list(filters)

    filter_fields = map(lambda x: x.field, filters_realized)
    # TODO: might want to log this
    filter_fields = filter(lambda x: x in FIELD_MAP, filter_fields)
    filter_fields_realized = list(map(lambda x: FIELD_MAP[x], filter_fields))

    operators = map(lambda x: x.operator, filters_realized)
    operators = map(lambda x: str(x), operators)
    operators = filter(lambda x: x in OPERATOR_MAP, operators)
    operators_realized = list(map(lambda x: OPERATOR_MAP[x], operators))

    operands_realized = list(map(lambda x: x.operand, filters_realized))

    fields_and_extraneous = zip(
        filter_fields_realized,
        operators_realized,
        operands_realized
    )

    fields_and_extraneous_named = map(
        lambda x: {
            'field': x[0],
            'operator': x[1],
            'operands': x[2]
        },
        fields_and_extraneous
    )

    filter_fields_str = map(
        lambda x: build_query_component(
            x['field'], # type: ignore
            x['operator'], # type: ignore
            x['operands'] # type: ignore
        ),
        fields_and_extraneous_named
    )
    clause = ' AND '.join(filter_fields_str)

    stmt = statement_template % (table, clause)

    return QueryInfo(filter_fields_realized, stmt)


def build_search_query(filters: typing.Iterable[models.Filter],
        table: str) -> QueryInfo:
    """Build a string SQL query from the given filters.

    @param filters: The filters to build the query out of.
    @type filters: Iterable over models.Filter
    @param table: The name of the table to query.
    @type table: str
    @return: SQL select query for the given table with the given filters.
    """
    return build_query(filters, table, 'SELECT * FROM %s WHERE %s')


def build_delete_query(filters: typing.Iterable[models.Filter], table: str,
        restore: bool, hard_delete: bool = False) -> QueryInfo:
    """Create a delete related query (either to delete or to restore).

    @param filters: The filters through which to target the action.
    @param table: The name of the table on which to operate.
    @param restore: Flag indicating if records are being restored. If true, data
        are being restored. If false, being deleted.
    @param hard_delete: Flag indicating if the delete should be permanent. If
        true, the data are permanently deleted. If false, will only be set to
        deleted but not actually removed. Ignored if restore == True.
    @returns: Newly generated SQL.
    """
    if restore:
        return build_query(filters, table, 'UPDATE %s SET deleted=0 WHERE %s')
    elif hard_delete:
        return build_query(filters, table, 'DELETE FROM %s WHERE %s')
    else:
        return build_query(filters, table, 'UPDATE %s SET deleted=1 WHERE %s')


def assert_int(target: typing.Any) -> int:
    """Ensure that target has a numeric type and get it as int."""
    assert isinstance(target, numbers.Number)
    return int(target) # type: ignore


def assert_float(target: typing.Any) -> float:
    """Ensure that target has a numeric type and get it as float."""
    assert isinstance(target, numbers.Number)
    return float(target) # type: ignore


def assert_str(target: typing.Any) -> str:
    """Ensure that target has a string type."""
    assert isinstance(target, str) or isinstance(target, numbers.Number)
    return str(target) # type: ignore


def run_search_query(filters_iter: typing.Iterable[models.Filter], table: str,
        exclude_deleted: bool = True) -> typing.List[models.SnapshotMetadata]:
    """Builds and runs a SQL select query on the given table with given filters.

    @param filters_iter: The filters to build the query out of.
    @type filters_iter: Iterable over models.Filter
    @param table: The name of the table to query.
    @type table: str
    @return: Results of SQL select query for the given table with the given
        filters.
    @rtype: Iterable over models.SnapshotMetadata
    """
    db_connection = db_util.get_db_connection()
    db_cursor = db_connection.cursor()

    filters = list(filters_iter)

    if exclude_deleted:
        filters.append(models.Filter('deleted', 'eq', 0))

    query_info = build_search_query(filters, table)
    raw_operands = map(lambda x: x.operand, filters)

    filter_fields_and_operands = zip(query_info.filter_fields, raw_operands)

    operands = map(
        lambda x: x[0].interpret_value(x[1]),
        filter_fields_and_operands
    )

    operands_flat = []
    for operand in operands:
        operands_flat.extend(operand)

    db_cursor.execute(query_info.query_str, operands_flat)

    ret_val = list(map(
        lambda x: models.SnapshotMetadata(
            assert_int(x[0]),
            assert_str(x[1]),
            assert_str(x[2]),
            assert_str(x[3]),
            assert_int(x[4]),
            assert_float(x[5]),
            assert_str(x[6]),
            assert_str(x[7]),
            assert_int(x[8]),
            assert_int(x[9]),
            assert_int(x[10]),
            assert_int(x[11]),
            assert_float(x[12]),
            assert_int(x[13]),
            assert_int(x[14]),
            assert_str(x[15]).split(','),
            assert_int(x[16]),
            assert_str(x[17]),
            assert_int(x[18]),
            assert_int(x[19])
        ),
        db_cursor.fetchall()
    ))
    db_connection.close()
    return ret_val


def run_delete_query(filters: typing.Iterable[models.Filter],
        table: str,
        restore: bool,
        hard_delete: bool = False) -> typing.Iterable[models.SnapshotMetadata]:
    """Builds and runs a SQL select query on the given table with given filters.

    @param filters: The filters to build the query out of.
    @type: Iterable over models.Filter
    @param table: The name of the table to query.
    @type table: str
    @param hard_delete: Flag indicating if the delete should be permanent. If
        true, the data are permanently deleted. If false, will only be set to
        deleted but not actually removed. Ignored if restore == True.
    @return: Results of SQL select query for the given table with the given
        filters.
    @rtype: Iterable over models.SnapshotMetadata
    """
    filters_realized = list(filters)

    records = run_search_query(filters_realized, table, False)

    query_info = build_delete_query(
        filters_realized,
        table,
        restore,
        hard_delete=hard_delete
    )
    raw_operands = map(lambda x: x.operand, filters_realized)

    filter_fields_and_operands = zip(query_info.filter_fields, raw_operands)

    operands = map(
        lambda x: x[0].interpret_value(x[1]),
        filter_fields_and_operands
    )

    operands_flat = []
    for operand in operands:
        operands_flat.extend(operand)

    with db_util.get_cursor() as db_cursor:
        db_cursor.execute(query_info.query_str, operands_flat)

    return records
