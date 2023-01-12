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

import logging

logger = logging.getLogger(__name__)


class SyntaxError(Exception):
    pass


def parse(s):
    func = s.split("(", 1)
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


def execute(args, model_object, sql, columns):
    logger.debug("execute", args)
    if not isinstance(args, list):
        return args
    elif "_" + args[0] in globals():
        return globals()["_" + args[0]](args[1:], model_object, sql, columns)
    else:
        raise SyntaxError(f"invalid function {args[0]}")


def check_column(col, columns):
    if col in columns:
        return col
    raise SyntaxError(f"Invalid column {col}")


def _q(args, model_object, sql, columns):
    logger.debug("q", args)
    if len(args) != 1:
        raise SyntaxError(f"invalid number of args {len(args)} for q")
    return execute(args[0], model_object, sql, columns)


def _eq(args, model_object, sql, columns):
    logger.debug("eq", args)
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for eq")
    m_column = getattr(
        model_object,
        check_column(execute(args[0], model_object, sql, columns), columns),
    )
    return sql.filter(m_column == execute(args[1], model_object, sql, columns))


def _in(args, model_object, sql, columns):
    logger.debug("in", args)
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for in")
    m_column = getattr(
        model_object,
        check_column(execute(args[0], model_object, sql, columns), columns),
    )
    if isinstance(m_column.type, ARRAY):
        return sql.filter(
            m_column.contains([execute(args[1], model_object, sql, columns)])
        )


def _and(args, model_object, sql, columns):
    logger.debug("and", args)
    return sql.and_(*[execute(a, model_object, sql, columns) for a in args])


def _or(args, model_object, sql, columns):
    logger.debug("or", args)
    return sql.or_(*[execute(a, model_object, sql, columns) for a in args])


def _not(args, model_object, sql, columns):
    logger.debug("not", args)
    if len(args) != 1:
        raise SyntaxError(f"invalid number of args {len(args)} for not")
    return sql.not_(execute(args[0], model_object, sql, columns))


# query.py ends here
