# -*- encoding: utf-8 -*-
#
# Copyright 2018 Red Hat, Inc.
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
import csv
import threading

import mock
import pytest

from datetime import datetime
from dci.common import csv_utils, vulnerability_scans
from dci.common.exceptions import DCIException
from dci.common.schemas import check_json_is_valid, args_schema
from dci.common.args import parse_args


def test_args():
    try:
        check_json_is_valid(
            args_schema,
            {
                "limit": "100",
                "offset": "0",
                "sort": "field_1,field_2",
                "where": "field_0:,field_1:value_1,field_2:value_2,field_3:",
                "embed": "resource_1,resource_2",
            },
        )
        check_json_is_valid(
            args_schema,
            {
                "limit": "100",
                "offset": "100",
                "sort": "field_1",
                "where": "field_1:value_1",
                "embed": "resource_1",
            },
        )
        check_json_is_valid(args_schema, {})
    except DCIException:
        pytest.fail("args_limit is invalid")


def test_args_invalid_offset_inf_to_zero():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "100", "offset": "-100"})


def test_args_invalid_limit_inf_to_zero():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "-100", "offset": "0"})


def test_args_invalid_limit_equal_to_zero():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "0", "offset": "10"})


def test_args_invalid_where_field():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"where": "f1"})


def test_parse_args():
    args = {
        "limit": "50",
        "offset": "10",
        "sort": "field_1,field_2",
        "where": "field_1:value_1,field_2:value_2",
        "embed": "resource_1,resource_2",
        "created_after": "2021-12-18T01:04:05.080452",
        "updated_after": "1640090291000",
    }
    args_expected = {
        "limit": 50,
        "offset": 10,
        "sort": ["field_1", "field_2"],
        "where": ["field_1:value_1", "field_2:value_2"],
        "embed": ["resource_1", "resource_2"],
        "created_after": datetime(2021, 12, 18, 1, 4, 5, 80452),
        "updated_after": datetime(2021, 12, 21, 12, 38, 11),
    }
    assert parse_args(args) == args_expected


def test_argument_and_scan_csv_readers_share_the_field_limit_lock():
    lock = mock.MagicMock()
    with mock.patch.object(csv_utils, "_CSV_FIELD_SIZE_LOCK", lock):
        vulnerability_scans.csv_to_json(b"field\nvalue\n", 1024)
        assert parse_args({"sort": 'first,"second,third"'})["sort"] == [
            "first",
            "second,third",
        ]

    assert lock.__enter__.call_count == 2
    assert lock.__exit__.call_count == 2


def test_argument_reader_keeps_its_field_limit_after_a_scan():
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(16)
        vulnerability_scans.csv_to_json(b"field\n" + b"x" * 17, 1024)
        assert csv.field_size_limit() == 16
        assert parse_args({"sort": "first,second"})["sort"] == ["first", "second"]
        with pytest.raises(csv.Error):
            parse_args({"sort": "x" * 17})
    finally:
        csv.field_size_limit(previous_limit)


def test_argument_reader_waits_until_the_scan_field_limit_is_restored():
    previous_limit = csv.field_size_limit()
    original_reader = csv.reader
    observed_limits = []
    results = []
    errors = []
    started = threading.Event()
    finished = threading.Event()

    def read_arguments():
        started.set()
        try:
            results.append(parse_args({"sort": "first,second"})["sort"])
        except Exception as error:
            errors.append(error)
        finally:
            finished.set()

    def record_limit(*args, **kwargs):
        observed_limits.append(csv.field_size_limit())
        return original_reader(*args, **kwargs)

    worker = threading.Thread(target=read_arguments, daemon=True)
    with mock.patch.object(csv, "reader", side_effect=record_limit):
        with csv_utils.csv_field_size_limit(previous_limit + 100):
            worker.start()
            assert started.wait(timeout=1)
            assert not finished.wait(timeout=0.05)
        worker.join(timeout=1)

    assert not worker.is_alive()
    assert errors == []
    assert results == [["first", "second"]]
    assert observed_limits == [previous_limit]
    assert csv.field_size_limit() == previous_limit
