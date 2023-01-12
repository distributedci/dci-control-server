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

from dci.api.v1 import query


def test_query_invalid():
    assert query.parse("toto") == "toto"


def test_query_valid():
    ret = query.parse("q(eq(name,openshift-vanilla))")
    assert ret == [
        "q",
        ["eq", "name", "openshift-vanilla"],
    ]


def test_query_complex():
    ret = query.parse("q(and(eq(name,openshift-vanilla),not(in(tags,debug))))")
    assert ret == [
        "q",
        ["and", ["eq", "name", "openshift-vanilla"], ["not", ["in", "tags", "debug"]]],
    ]


def test_split():
    assert query.split("a,b") == ["a", "b"]


def test_execute_simple():
    ret = query.execute(query.parse("q(eq(name,ocp))"))
    assert ret == "name='ocp'"


def test_execute_invalid():
    try:
        query.execute(query.parse("equal(name,ocp)"))
    except query.SyntaxError:
        return
    assert False


def test_execute_and():
    ret = query.execute(query.parse("q(and(eq(name,install),eq(type,ocp)))"))
    assert ret == "name='install' AND type='ocp'"


def test_execute_or():
    ret = query.execute(query.parse("q(or(eq(name,install),eq(type,ocp)))"))
    assert ret == "name='install' OR type='ocp'"


def test_execute_not():
    ret = query.execute(query.parse("q(not(eq(name,install)))"))
    assert ret == "NOT name='install'"


# test_query.py ends here
