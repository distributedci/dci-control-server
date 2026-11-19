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

import datetime
import uuid

import mock
import pytest
from sqlalchemy import select

from dci.db import declarative as d
from dci.db import models2


def test_handle_pagination():
    m = mock.MagicMock()
    m.limit = mock.MagicMock()
    m.offset = mock.MagicMock(return_value=m)
    d.handle_pagination(m, {"limit": 20})
    m.offset.assert_called_once_with(0)
    m.limit.assert_called_once_with(20)
    for reset_m in (m, m.limit, m.offset):
        reset_m.reset_mock()
    d.handle_pagination(m, {"limit": 300, "offset": 12})
    m.offset.assert_called_once_with(12)
    m.limit.assert_called_once_with(200)


@pytest.mark.parametrize("model", [models2.JobEvent, models2.VulnerabilityScan])
@pytest.mark.parametrize(
    ("sort", "expected_order"),
    [
        (None, [("created_at", "desc"), ("id", "desc")]),
        ([], [("created_at", "desc"), ("id", "desc")]),
        (["created_at"], [("created_at", "asc")]),
        (["-id", "created_at"], [("id", "desc"), ("created_at", "asc")]),
    ],
)
def test_handle_args_sorting(model, sort, expected_order):
    args = {} if sort is None else {"sort": sort}
    query = d.handle_args(select(model), model, args)
    expected_clauses = [
        getattr(getattr(model, name), direction)() for name, direction in expected_order
    ]

    assert len(query._order_by_clauses) == len(expected_clauses)
    assert all(
        clause.compare(expected)
        for clause, expected in zip(query._order_by_clauses, expected_clauses)
    )


def test_handle_args_default_sort_paginates_matching_dates(empty_db, session):
    earlier = datetime.datetime(2026, 1, 1)
    later = earlier + datetime.timedelta(seconds=1)
    job_id = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    topic_id = uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    events = [
        models2.JobEvent(
            id=event_id, created_at=created_at, job_id=job_id, topic_id=topic_id
        )
        for event_id, created_at in (
            (10, later),
            (20, later),
            (30, earlier),
            (40, later),
        )
    ]

    with session:
        session.add_all(events)
        session.commit()
        query = d.handle_args(select(models2.JobEvent), models2.JobEvent, {})
        results = []
        for offset in (0, 2):
            page = d.handle_pagination(query, {"limit": 2, "offset": offset})
            results.extend(session.scalars(page).all())
        assert [event.id for event in results] == [40, 20, 10, 30]

        query = d.handle_args(
            select(models2.JobEvent),
            models2.JobEvent,
            {"sort": ["created_at", "id"]},
        )
        assert [event.id for event in session.scalars(query)] == [30, 10, 20, 40]
