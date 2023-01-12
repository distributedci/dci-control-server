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

import logging

logger = logging.getLogger(__name__)


class SyntaxError(Exception):
    pass


def parse(s):
    func = s.split("(", 1)
    if len(func) != 2:
        return s
    print(f"{func}")
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


def execute(args):
    logger.debug("execute", args)
    if not isinstance(args, list):
        return args
    elif "_" + args[0] in globals():
        return globals()["_" + args[0]](args[1:])
    else:
        raise SyntaxError(f"invalid function {args[0]}")


def _q(args):
    logger.debug("q", args)
    if len(args) != 1:
        raise SyntaxError(f"invalid number of args {len(args)} for q")
    return execute(args[0])


def _eq(args):
    logger.debug("eq", args)
    if len(args) != 2:
        raise SyntaxError(f"invalid number of args {len(args)} for eq")
        return None
    return execute(args[0]) + "='" + execute(args[1]) + "'"


def _and(args):
    logger.debug("and", args)
    return " AND ".join([execute(a) for a in args])


def _or(args):
    logger.debug("or", args)
    return " OR ".join([execute(a) for a in args])


def _not(args):
    logger.debug("not", args)
    if len(args) != 1:
        raise SyntaxError(f"invalid number of args {len(args)} for not")
    return "NOT " + execute(args[0])


# query.py ends here
