# -*- encoding: utf-8 -*-
#
# Copyright Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci.db import query_dsl

import pyparsing as pp
import pytest


def test_query_invalid():
    with pytest.raises(pp.ParseException):
        query_dsl.parse("toto")


def test_query_valid():
    ret = query_dsl.parse("eq(name,openshift-vanilla)")
    assert ret == ["eq", "name", "openshift-vanilla"]


def test_query_complex():
    ret = query_dsl.parse("and(eq(name,openshift-vanilla),not_contains(tags,debug)))")
    assert ret == [
        "and",
        ["eq", "name", "openshift-vanilla"],
        ["not_contains", "tags", "debug"],
    ]
