# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci.common import exceptions as dci_exc

import pyparsing as pp
from sqlalchemy import sql


_field = pp.Word(pp.alphanums + "_")
_value = pp.Word(pp.alphanums + "_" + "-")
_comma = pp.Suppress(pp.Literal(","))
_lp = pp.Suppress(pp.Literal("("))
_rp = pp.Suppress(pp.Literal(")"))

_operations = {"contains", "not_contains", "lt", "le", "gt", "ge", "eq", "ne"}
_operations = pp.oneOf(" ".join(_operations))
_op = _operations + _lp + _field + _comma + _value + _rp

_logical_binary_operations = {"and", "or"}
_lbop = pp.oneOf(" ".join(_logical_binary_operations))

query = pp.Forward()
query << (
    _op
    | pp.Group(
        _lbop + _lp + pp.Group(_op | query) + _comma + pp.Group(_op | query) + _rp
    )
)


def parse(q):
    res = query.parseString(q).asList()[0]
    if isinstance(res, str):
        return query.parseString(q).asList()
    return res


def build(sa_query, parsed_query, model_object, do_filter=True):
    columns = model_object.__mapper__.columns.keys()
    op, field, value = parsed_query[0], parsed_query[1], parsed_query[2]

    if op == "and":
        return sa_query.filter(
            sql.and_(
                build(sa_query, field, model_object, False),
                build(sa_query, value, model_object, False),
            )
        )
    elif op == "or":
        return sa_query.filter(
            sql.or_(
                build(sa_query, field, model_object, False),
                build(sa_query, value, model_object, False),
            )
        )

    if field not in columns:
        raise dci_exc.DCIException("Invalid field: %s" % field)
    m_column = getattr(model_object, field)

    res = None
    if op == "eq":
        res = m_column == value
    elif op == "ne":
        res = m_column != value
    elif op == "lt":
        res = m_column < value
    elif op == "le":
        res = m_column <= value
    elif op == "gt":
        res = m_column > value
    elif op == "ge":
        res = m_column >= value
    elif op == "contains":
        res = m_column.contains([value])
    elif op == "not_contains":
        res = not m_column.contains([value])
    else:
        raise dci_exc.DCIException("Invalid operation: %s" % op)

    if do_filter:
        return sa_query.filter(res)
    else:
        return res
