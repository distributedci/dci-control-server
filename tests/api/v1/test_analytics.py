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

from __future__ import unicode_literals

import mock
import uuid

from dci.api.v1 import analytics
from dci.analytics import query_es_dsl as qed


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_duration_cumulated_calls_analytics_backend(
    mock_requests, client_admin, team2_remoteci_id, rhel_80_topic_id
):
    mock_res = mock.MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "total": {"value": 0, "relation": "eq"},
        "max_score": None,
        "hits": [],
    }
    mock_requests.return_value = mock_res

    res = client_admin.get(
        "/api/v1/analytics/tasks_duration_cumulated?remoteci_id=%s&topic_id=%s"
        % (team2_remoteci_id, rhel_80_topic_id)
    )

    assert res.status_code == 200
    assert res.data == {
        "total": {"value": 0, "relation": "eq"},
        "max_score": None,
        "hits": [],
    }
    mock_requests.assert_called_once_with(
        "GET",
        "/duration_cumulated",
        params={
            "topic_id": str(rhel_80_topic_id),
            "remoteci_id": str(team2_remoteci_id),
            "offset": 0,
            "limit": 20,
        },
    )


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_components_coverage_calls_analytics_backend(
    mock_requests, client_admin, rhel_80_topic_id
):
    mock_res = mock.MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "total": {"value": 0, "relation": "eq"},
        "max_score": None,
        "hits": [],
    }
    mock_requests.return_value = mock_res

    res = client_admin.get(
        "/api/v1/analytics/tasks_components_coverage?topic_id=%s" % rhel_80_topic_id
    )

    assert res.status_code == 200
    assert res.data == {
        "total": {"value": 0, "relation": "eq"},
        "max_score": None,
        "hits": [],
    }
    mock_requests.assert_called_once_with(
        "GET",
        "/components_coverage",
        params={"topic_id": str(rhel_80_topic_id), "team_id": "red_hat", "types": []},
    )


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_junit_comparison_streams_response(
    mock_req, client_user1, team1_remoteci_id, rhel_80_topic_id
):
    mock_res = mock.MagicMock()
    mock_res.status_code = 200
    mock_req.return_value = mock_res

    res = client_user1.post(
        "/api/v1/analytics/junit_comparison",
        json={
            "topic_1_id": str(rhel_80_topic_id),
            "topic_1_start_date": "1970-01-01",
            "topic_1_end_date": "1970-01-01",
            "remoteci_1_id": str(team1_remoteci_id),
            "topic_1_baseline_computation": "mean",
            "tags_1": [],
            "topic_2_id": str(rhel_80_topic_id),
            "topic_2_start_date": "1970-01-01",
            "topic_2_end_date": "1970-01-01",
            "remoteci_2_id": str(team1_remoteci_id),
            "topic_2_baseline_computation": "mean",
            "tags_2": [],
            "test_name": "test",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/json"


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_pipelines_status_streams_response(mock_req, client_admin):
    mock_res = mock.MagicMock()
    mock_res.status_code = 200
    mock_req.return_value = mock_res

    res = client_admin.post(
        "/api/v1/analytics/pipelines_status",
        json={
            "start_date": "1970-01-01",
            "end_date": "1970-01-01",
            "teams_ids": [],
            "pipelines_names": [],
        },
    )
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/json"


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_pipelines_status_empty_teams_ids_is_unauthorized(mock_req, client_user1):
    # A regular user sending teams_ids=[] bypasses the team-membership check
    # and reaches the analytics backend with no team filter.
    res = client_user1.post(
        "/api/v1/analytics/pipelines_status",
        json={
            "start_date": "1970-01-01",
            "end_date": "1970-01-01",
            "teams_ids": [],
            "pipelines_names": [],
        },
    )
    assert res.status_code == 401
    mock_req.assert_not_called()


def test_tasks_analytics_pipelines_status(client_user1, team_admin_id):
    res = client_user1.post(
        "/api/v1/analytics/pipelines_status",
        data={
            "start_date": "1970-01-01",
            "end_date": "1970-01-01",
            "teams_ids": [team_admin_id],
            "pipelines_names": ["pipeline_name"],
        },
    )
    assert res.status_code == 401


def test_tasks_jobs(client_user1, client_admin):
    res = client_admin.get(
        "/api/v1/analytics/jobs?query=foo",
    )
    assert res.status_code == 400


def test_handle_es_sort():
    res = analytics.handle_es_sort({"sort": "titi"})
    assert res == [{"titi": {"order": "asc", "format": "strict_date_optional_time"}}]

    res = analytics.handle_es_sort({"sort": "-titi"})
    assert res == [{"titi": {"order": "desc", "format": "strict_date_optional_time"}}]

    res = analytics.handle_es_sort({})
    assert res == [
        {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
    ]


def test_handle_es_timeframe():
    query = qed.build("name='titi'")
    res = analytics.handle_es_timeframe(
        query, {"from": "2024-01-01", "to": "2024-02-01"}
    )
    assert res == {
        "bool": {
            "filter": [
                {"range": {"created_at": {"gte": "2024-01-01", "lte": "2024-02-01"}}},
                query,
            ]
        }
    }


def test_handle_includes_excludes():
    ret = analytics.handle_includes_excludes(
        {"includes": "titi,tata", "excludes": "toto"}
    )
    assert ret == {"excludes": ["toto"], "includes": ["titi", "tata"]}

    ret = analytics.handle_includes_excludes({})
    assert ret == {}


def test_build_es_query():
    args = {
        "offset": 10,
        "limit": 10,
        "query": "(((components.type='ocp') and (components.tags in ['build:ga'])) and ((components.type='f5-spk')) and (tags in ['daily']))",
        "sort": "-created_at",
        "from": "2024-01-01",
        "to": "2024-02-01",
        "includes": "team,topic",
        "excludes": "jobstates",
    }
    ret = analytics.build_es_query(args)
    assert ret == {
        "from": 10,
        "size": 10,
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "created_at": {"gte": "2024-01-01", "lte": "2024-02-01"}
                        }
                    },
                    {
                        "bool": {
                            "filter": [
                                {
                                    "nested": {
                                        "path": "components",
                                        "query": {
                                            "bool": {
                                                "filter": [
                                                    {
                                                        "term": {
                                                            "components.type": "ocp"
                                                        }
                                                    },
                                                    {
                                                        "terms": {
                                                            "components.tags": [
                                                                "build:ga"
                                                            ]
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "components",
                                        "query": {
                                            "term": {"components.type": "f5-spk"}
                                        },
                                    }
                                },
                                {"terms": {"tags": ["daily"]}},
                            ]
                        }
                    },
                ]
            }
        },
        "sort": [
            {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
        ],
        "_source": {"excludes": ["jobstates"], "includes": ["team", "topic"]},
    }


def test_build_es_query_with_teams():
    args = {
        "offset": 10,
        "limit": 10,
        "query": "(name='toto')",
        "sort": "-created_at",
        "from": "2024-01-01",
        "to": "2024-02-01",
        "includes": "team,topic",
        "excludes": "jobstates",
    }
    teams_ids = [uuid.uuid4(), uuid.uuid4()]
    ret = analytics.build_es_query(args, teams_ids)
    assert ret == {
        "from": 10,
        "size": 10,
        "query": {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [
                                {"term": {"team_id": str(teams_ids[0])}},
                                {"term": {"team_id": str(teams_ids[1])}},
                            ]
                        }
                    },
                    {
                        "bool": {
                            "filter": [
                                {
                                    "range": {
                                        "created_at": {
                                            "gte": "2024-01-01",
                                            "lte": "2024-02-01",
                                        }
                                    }
                                },
                                {"term": {"name": "toto"}},
                            ]
                        }
                    },
                ]
            }
        },
        "sort": [
            {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
        ],
        "_source": {"excludes": ["jobstates"], "includes": ["team", "topic"]},
    }


def test_build_autocompletion_query():
    args = {"field": "field"}
    res = analytics.build_autocompletion_query(
        args, "6e6b1cbc-9e0d-49fd-8cff-9ebf37caf147"
    )
    assert res == {
        "field": "field",
        "team_id": "6e6b1cbc-9e0d-49fd-8cff-9ebf37caf147",
        "size": 10,
    }


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_autocomplete_field(mock_requests, client_user1):
    mock_autocomplete = mock.MagicMock()
    mock_autocomplete.status_code = 200
    mock_autocomplete.content = b'["job1", "job2"]'
    mock_requests.return_value = mock_autocomplete
    res = client_user1.get("/api/v1/analytics/jobs/autocomplete?field=name")
    assert res.status_code == 200
    assert res.data == ["job1", "job2"]


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_jobs_streams_response(mock_req, client_admin):
    mock_res = mock.MagicMock()
    mock_res.status_code = 200
    mock_req.return_value = mock_res

    res = client_admin.get("/api/v1/analytics/jobs?query=(name%3D'test')")
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/json"


@mock.patch("dci.api.v1.analytics.analytics_request")
def test_tasks_jobs2_streams_response(mock_req, client_admin):
    mock_res = mock.MagicMock()
    mock_res.status_code = 200
    mock_req.return_value = mock_res

    res = client_admin.get("/api/v1/analytics/jobs2", json={})
    assert res.status_code == 200
    assert res.headers.get("Content-Type") == "application/json"


def test_aggs():
    args = {
        "query": "(name='toto')",
        "json-aggs": '{"aggs": {"aggs_teams": {"terms": {"field": "team_id"}}}}',
    }
    teams_ids = [uuid.uuid4(), uuid.uuid4()]
    ret = analytics.build_es_query(args, teams_ids)
    assert ret == {
        "from": 0,
        "size": 20,
        "query": {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [
                                {"term": {"team_id": str(teams_ids[0])}},
                                {"term": {"team_id": str(teams_ids[1])}},
                            ]
                        }
                    },
                    {"term": {"name": "toto"}},
                ]
            }
        },
        "aggs": {"aggs_teams": {"terms": {"field": "team_id"}}},
        "sort": [
            {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
        ],
    }
