# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pyparsing as pp

_field = pp.Word(pp.alphanums + "_" + ".")
_integer = pp.Word(pp.nums).setParseAction(lambda tokens: int(tokens[0]))


def _int_or_float(v):
    try:
        return int(v)
    except ValueError:
        return float(v)


_integer_or_float = pp.Word(pp.nums + "." + "-").setParseAction(
    lambda tokens: _int_or_float(tokens[0])
)
_value_with_quotes = pp.QuotedString("'", unquoteResults=True)
_value = _integer_or_float | _value_with_quotes

_value_for_list = pp.Word(pp.alphanums + "_" + "." + "-" + ":" + " ")
_value_for_list = (
    pp.Suppress(pp.Literal("'")) + _value_for_list + pp.Suppress(pp.Literal("'"))
)

_comma = pp.Suppress(pp.Literal(","))
_lp = pp.Suppress(pp.Literal("("))
_rp = pp.Suppress(pp.Literal(")"))

_lb = pp.Suppress(pp.Literal("["))
_rb = pp.Suppress(pp.Literal("]"))

_comma_value = _comma + _value_for_list
_list = _lb + _value_for_list + pp.ZeroOrMore(_comma_value) + _rb

_comparison_operators = {"=", "!=", "<=", "<", ">=", ">", "=~"}
_comparison_operators = pp.oneOf(" ".join(_comparison_operators))
_comparison = _field + _comparison_operators + _value

_membership_operators = {"not_in", "in"}
_membership_operators = pp.oneOf(" ".join(_membership_operators))
_membership_operation = _field + _membership_operators + pp.Group(_list)

_logical_operators = {"and", "or"}
_logical_operators = pp.oneOf(" ".join(_logical_operators))
_logical_operation = (
    pp.Group(_lp + (_comparison | _membership_operation) + _rp)
    + _logical_operators
    + pp.Group(_lp + (_comparison | _membership_operation) + _rp)
    | _lp + (_comparison | _membership_operation) + _rp
    | (_comparison | _membership_operation)
)

query = pp.Forward()
_not_operation = pp.Group(pp.Keyword("not") + _lp + pp.Group(query) + _rp)
query << (
    (_lp + pp.Group(query) + _rp + pp.ZeroOrMore(_logical_operators + query))
    | _not_operation + pp.ZeroOrMore(_logical_operators + query)
    | _logical_operation
)


def parse(q):
    return query.parseString(q, parseAll=True).asList()


_op_to_es_range_op = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}


def _get_nested_prefix(operand):
    return ".".join(operand.split(".")[:-1])


def _get_root_prefix(operand):
    return operand.split(".")[0]


def _unique_inner_hits_name(path, seen_count_by_path):
    """Names for inner_hits are unique per query: counter by path Elasticsearch."""
    n = seen_count_by_path.get(path, 0)
    seen_count_by_path[path] = n + 1
    return path if n == 0 else "%s_%d" % (path, n)


def _handle_comparison_operator(
    handle_nested, operator, operand_1, operand_2, seen_count_by_path
):
    if handle_nested and "." in operand_1:
        path = _get_nested_prefix(operand_1)
        return {
            "nested": {
                "path": path,
                "query": {
                    "range": {operand_1: {_op_to_es_range_op[operator]: operand_2}}
                },
                "inner_hits": {
                    "name": _unique_inner_hits_name(path, seen_count_by_path)
                },
            }
        }
    return {"range": {operand_1: {_op_to_es_range_op[operator]: operand_2}}}


def _generate_from_operators(
    parsed_query, handle_nested=False, seen_count_by_path=None
):
    if seen_count_by_path is None:
        seen_count_by_path = {}
    if len(parsed_query) == 2 and parsed_query[0] == "not":
        return {
            "bool": {
                "must_not": [
                    _generate_from_operators(
                        parsed_query[1],
                        handle_nested=handle_nested,
                        seen_count_by_path=seen_count_by_path,
                    )
                ]
            }
        }

    operand_1 = parsed_query[0]
    operator = parsed_query[1]
    operand_2 = parsed_query[2]

    if operator == "=":
        if handle_nested and "." in operand_1:
            path = _get_nested_prefix(operand_1)
            return {
                "nested": {
                    "path": path,
                    "query": {"term": {operand_1: operand_2}},
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        return {"term": {operand_1: operand_2}}
    if operator in _op_to_es_range_op.keys():
        return _handle_comparison_operator(
            handle_nested,
            operator,
            operand_1,
            operand_2,
            seen_count_by_path,
        )
    elif operator == "=~":
        _regexp = {
            "regexp": {
                operand_1: {
                    "value": operand_2,
                    "flags": "ALL",
                    "case_insensitive": True,
                }
            }
        }
        if handle_nested and "." in operand_1:
            path = _get_nested_prefix(operand_1)
            return {
                "nested": {
                    "path": path,
                    "query": _regexp,
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        return _regexp
    elif operator == "not_in":
        if handle_nested and "." in operand_1:
            path = _get_nested_prefix(operand_1)
            return {
                "nested": {
                    "path": path,
                    "query": {"bool": {"must_not": {"terms": {operand_1: operand_2}}}},
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        return {"bool": {"must_not": {"terms": {operand_1: operand_2}}}}
    elif operator == "in":
        if handle_nested and "." in operand_1:
            path = _get_nested_prefix(operand_1)
            return {
                "nested": {
                    "path": path,
                    "query": {"terms": {operand_1: operand_2}},
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        return {"terms": {operand_1: operand_2}}
    elif operator == "!=":
        if handle_nested and "." in operand_1:
            path = _get_nested_prefix(operand_1)
            return {
                "nested": {
                    "path": path,
                    "query": {"bool": {"must_not": {"term": {operand_1: operand_2}}}},
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        return {"bool": {"must_not": {"term": {operand_1: operand_2}}}}


def _split_on_or(parsed_query):
    before_or = []
    after_or = []
    for i in range(len(parsed_query)):
        if parsed_query[i] != "or":
            before_or.append(parsed_query[i])
        elif parsed_query[i] == "or":
            after_or = parsed_query[i + 1 :]
            break
    return before_or, after_or


def _get_logical_operands(parsed_query):
    operands = []
    for q in parsed_query:
        if q != "or" and q != "and":
            operands.append(q)
    return operands


def _is_nested_query(operands_1, operands_2=None):
    path = None
    if (
        isinstance(operands_1, list)
        and isinstance(operands_1[0], list)
        and isinstance(operands_1[0][0], str)
        and "." in operands_1[0][0]
    ):
        path = _get_nested_prefix(operands_1[0][0])
    if path:
        if operands_2:
            for o in operands_2:
                if o[0].split(".")[0] != path:
                    return None
    return path


def _generate_es_query(parsed_query, handle_nested=True, seen_count_by_path=None):
    if seen_count_by_path is None:
        seen_count_by_path = {}
    if (
        len(parsed_query) > 0
        and isinstance(parsed_query, list)
        and isinstance(parsed_query[0], str)
    ):
        return _generate_from_operators(parsed_query, handle_nested, seen_count_by_path)
    if (
        len(parsed_query) == 1
        and isinstance(parsed_query, list)
        and isinstance(parsed_query[0], list)
    ):
        return _generate_es_query(parsed_query[0], handle_nested, seen_count_by_path)

    if "or" in parsed_query:
        left_operands, right_operands = _split_on_or(parsed_query)
        path = _is_nested_query(left_operands, right_operands)
        if path:
            return {
                "nested": {
                    "path": path,
                    "query": {
                        "bool": {
                            "should": [
                                _generate_es_query(
                                    left_operands,
                                    handle_nested=False,
                                    seen_count_by_path=seen_count_by_path,
                                )
                            ]
                            + [
                                _generate_es_query(
                                    right_operands,
                                    handle_nested=False,
                                    seen_count_by_path=seen_count_by_path,
                                )
                            ],
                        }
                    },
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        else:
            return {
                "bool": {
                    "should": [
                        _generate_es_query(
                            left_operands, seen_count_by_path=seen_count_by_path
                        )
                    ]
                    + [
                        _generate_es_query(
                            right_operands, seen_count_by_path=seen_count_by_path
                        )
                    ],
                }
            }
    else:
        operands = _get_logical_operands(parsed_query)
        path = _is_nested_query(operands)
        if (
            path
            and len(operands) > 1
            and isinstance(operands[0][0], str)
            and isinstance(operands[1][0], str)
            and _get_root_prefix(operands[0][0]) != _get_root_prefix(operands[1][0])
        ) or (type(operands[0][0]) != type(operands[1][0])):
            path = None
        if path:
            first_element = operands[0]
            _filter = [
                _generate_es_query(
                    first_element,
                    handle_nested=False,
                    seen_count_by_path=seen_count_by_path,
                )
            ]
            operands = operands[1:]
            if len(operands) == 1 and isinstance(operands[0][0], list):
                operands = operands[0]
            i = 0
            while i < len(operands):
                if path == _get_nested_prefix(operands[i][0]):
                    _filter.append(
                        _generate_es_query(
                            operands[i],
                            handle_nested=False,
                            seen_count_by_path=seen_count_by_path,
                        )
                    )
                else:
                    break
                i += 1
            if i < len(operands):
                _filter.append(
                    _generate_es_query(
                        operands[i:],
                        handle_nested=True,
                        seen_count_by_path=seen_count_by_path,
                    )
                )

            return {
                "nested": {
                    "path": path,
                    "query": {"bool": {"filter": _filter}},
                    "inner_hits": {
                        "name": _unique_inner_hits_name(path, seen_count_by_path)
                    },
                }
            }
        else:
            return {
                "bool": {
                    "filter": [
                        _generate_es_query(o, seen_count_by_path=seen_count_by_path)
                        for o in operands
                    ]
                }
            }


def build(query):
    parsed_query = parse(query)
    seen_count_by_path = {}
    return _generate_es_query(parsed_query, seen_count_by_path=seen_count_by_path)
