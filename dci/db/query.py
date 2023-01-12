#
# Copyright (C) 2023 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
"""

from sqlalchemy.types import ARRAY
from sqlalchemy import or_

import logging

logger = logging.getLogger(__name__)
log = logger.debug


class SyntaxError(Exception):
    pass


def parse(s):
    func = s.split("(", 1)
    log(f"parse {func}")
    if len(func) != 2:
        return s
    if len(func[1]) == 0 or not func[1][-1] == ")":
        raise SyntaxError(f"Invalid syntax {s}")
    args = split(func[1][:-1])
    return [func[0]] + [parse(a) for a in args]


def split(s):
    count = 0
    start = 0
    ret = []
    for idx in range(1, len(s)):
        if s[idx] == "(":
            count += 1
        elif s[idx] == ")":
            count -= 1
        elif count == 0 and s[idx] == ",":
            ret.append(s[start:idx])
            start = idx + 1
    ret.append(s[start : idx + 1])
    return ret


def execute(args, model_object, sql, columns, do_filter=True):
    log("execute %s", args)
    if isinstance(args, list) and "_" + args[0] in globals():
        return globals()["_" + args[0]](args[1:], model_object, sql, columns, do_filter)
    else:
        raise SyntaxError(f"Invalid function {args[0]}")


def left(args, model_object, columns):
    log("execute %s", args)
    if isinstance(args, str):
        col = check_column(args, columns)
        return getattr(model_object, col)
    else:
        raise SyntaxError(f"Invalid column {args}")


def right(args):
    log("execute %s", args)
    if isinstance(args, str):
        return args
    else:
        raise SyntaxError(f"Invalid value {args[0]}")


def check_column(col, columns):
    if col in columns:
        return col
    raise SyntaxError(f"Invalid column name {col}")


def _q(args, model_object, sql, columns, do_filter):
    log(f"q {args}")
    if len(args) != 1:
        raise SyntaxError(f"invalid number of args {len(args)} for q")
    return execute(args[0], model_object, sql, columns)


def _eq(args, model_object, sql, columns, do_filter):
    log(f"eq {args}")
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for eq")
    m_column = left(args[0], model_object, columns)
    val = right(args[1])
    if do_filter:
        return sql.filter(m_column == val)
    else:
        return m_column == val


def _ne(args, model_object, sql, columns, do_filter):
    log(f"ne {args}")
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for ne")
    m_column = left(args[0], model_object, sql, columns)
    val = right(args[1])
    if do_filter:
        return sql.filter(m_column != val)
    else:
        return m_column != val


def _like(args, model_object, sql, columns, do_filter):
    log(f"like {args}")
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for like")
    m_column = left(args[0], model_object, columns)
    val = right(args[1])
    if do_filter:
        return sql.filter(m_column.like(val))
    else:
        return m_column.like(val)


def _ilike(args, model_object, sql, columns, do_filter):
    log(f"ilike {args}")
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for ilike")
    m_column = left(args[0], model_object, columns)
    val = right(args[1])
    if do_filter:
        return sql.filter(m_column.ilike(val))
    else:
        return m_column.ilike(val)


def _in(args, model_object, sql, columns, do_filter):
    log(f"in {args}")
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for in")
    m_column = left(args[0], model_object, columns)
    val = right(args[1])
    if isinstance(m_column.type, ARRAY):
        log(f"{m_column} contains {val}")
        if do_filter:
            return sql.filter(m_column.contains([val]))
        else:
            return m_column.contains([val])
    raise SyntaxError(f"{args[0]} is not an array")


def _not_in(args, model_object, sql, columns, do_filter):
    log(f"not_in {args}")
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for not_in")
    m_column = left(args[0], model_object, columns)
    val = right(args[1])
    if isinstance(m_column.type, ARRAY):
        log(f"{m_column} contains {val}")
        if do_filter:
            return sql.filter(~m_column.contains([val]))
        else:
            return ~m_column.contains([val])
    raise SyntaxError(f"{args[0]} is not an array")


def _and(args, model_object, sql, columns, do_filter):
    log(f"and {args}")
    for a in args:
        sql = execute(a, model_object, sql, columns, do_filter)
    return sql


def _or(args, model_object, sql, columns, do_filter):
    log(f"or {args}")
    clauses = []
    for a in args:
        clauses.append(execute(a, model_object, sql, columns, False))
    log(f"clauses {clauses}")
    return sql.filter(or_(*clauses))


# query.py ends here
