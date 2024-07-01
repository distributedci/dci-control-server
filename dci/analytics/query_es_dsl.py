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
_value = pp.Word(pp.alphanums + "_" + "-" + "%" + "." + ":")
_word = pp.Word(pp.alphanums + "_" + "-" + ".")
_comma = pp.Suppress(pp.Literal(","))
_lp = pp.Suppress(pp.Literal("("))
_rp = pp.Suppress(pp.Literal(")"))

_lb = pp.Suppress(pp.Literal("["))
_rb = pp.Suppress(pp.Literal("]"))

_comma_string = _comma + _word
_list = _lb + _word + pp.ZeroOrMore(_comma_string) + _rb

_comparison_operators = {"=", "!=", "<=" "<", ">=", ">"}
_comparison_operators = pp.oneOf(" ".join(_comparison_operators))
_comparison = _field + _comparison_operators + _value

_membership_operators = {"not_in"}
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
query << (
    (_lp + pp.Group(query) + _rp + _logical_operators + _lp + pp.Group(query) + _rp)
    | _logical_operation
)


def parse(q):
    return query.parseString(q).asList()


def _generate_es_query(parsed_query):
    operand_1 = parsed_query[0]
    operator = parsed_query[1]
    operand_2 = parsed_query[2]

    nested = None
    if isinstance(operand_1, list) and "." in operand_1[0] and "." in operand_2[0]:
        if operand_1[0].split(".")[0] == operand_2[0].split(".")[0]:
            nested = {"nested": {"path": operand_1[0].split(".")[0]}}

    if operator == "or":
        bool_should = {
            "bool": {
                "should": [
                    _generate_es_query(operand_1),
                    _generate_es_query(operand_2),
                ]
            }
        }
        if nested:
            nested["nested"]["query"] = bool_should
            return nested
        else:
            return bool_should
    elif operator == "and":
        bool_filter = {
            "bool": {
                "filter": [
                    _generate_es_query(operand_1),
                    _generate_es_query(operand_2),
                ]
            }
        }
        if nested:
            nested["nested"]["query"] = bool_filter
            return nested
        else:
            return bool_filter
    elif operator == "=":
        return {"term": {operand_1: operand_2}}
    elif operator == "not_in":
        if "." in operand_1:
            return {
                "nested": {
                    "path": operand_1.split(".")[0],
                    "query": {"must_not": {"terms": {operand_1: operand_2}}},
                }
            }
        return {"must_not": {"terms": {operand_1: operand_2}}}


def build(query):
    parsed_query = parse(query)
    return {"query": _generate_es_query(parsed_query)}
