# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2023 Red Hat, Inc
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


def test_create_jobstates(client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "running", "comment": "kikoolol"}

    with mock.patch("dci.app.dci_kombu.KombuProducer") as mock_kp:
        mock_kp = mock_kp.return_value
        js = client_user1.post("/api/v1/jobstates", data=data).data
        mock_kp.publish_jobs_finished.assert_not_called()
    js_id = js["jobstate"]["id"]

    js = client_user1.get("/api/v1/jobstates/%s" % js_id).data
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data

    assert js["jobstate"]["comment"] == "kikoolol"
    assert job["job"]["status"] == "running"


def test_nrt_create_jobstates_from_other_team(client_user2, team1_job_id):
    data = {"job_id": team1_job_id, "status": "running", "comment": "kikoolol"}

    assert client_user2.post("/api/v1/jobstates", data=data).status_code == 401


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_create_jobstates_failure(mock_kp, client_user1, team1_job_id):
    mock_kp = mock_kp.return_value
    data = {"job_id": team1_job_id, "status": "failure"}
    client_user1.post("/api/v1/jobstates", data=data)
    # Notification should be sent just one time
    client_user1.post("/api/v1/jobstates", data=data)
    mock_kp.publish_jobs_finished.assert_called_once()

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data
    assert job["job"]["status"] == "failure"


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_create_jobstates_notification(mock_kp, client_user1, team1_job_id):
    mock_kp = mock_kp.return_value
    data = {"job_id": team1_job_id, "status": "failure"}

    client_user1.post("/api/v1/jobstates", data=data)
    mock_kp.publish_jobs_finished.assert_called_with({"job_id": team1_job_id})


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_create_jobstates_new_to_failure(_, client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "new"}
    js = client_user1.post("/api/v1/jobstates", data=data).data
    assert js["jobstate"]["status"] == "new"
    data = {"job_id": team1_job_id, "status": "failure"}
    js = client_user1.post("/api/v1/jobstates", data=data).data
    js = client_user1.get("/api/v1/jobstates/%s" % js["jobstate"]["id"]).data
    assert js["jobstate"]["status"] == "error"


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_create_jobstates_error(_, client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "error"}

    js = client_user1.post("/api/v1/jobstates", data=data).data
    js = client_user1.get("/api/v1/jobstates/%s" % js["jobstate"]["id"]).data
    assert js["jobstate"]["status"] == "error"


def test_create_jobstates_empty_comment(client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "running"}

    js = client_user1.post("/api/v1/jobstates", data=data).data
    assert js["jobstate"]["comment"] is None

    js = client_user1.get("/api/v1/jobstates/%s" % js["jobstate"]["id"]).data
    assert js["jobstate"]["comment"] is None


def test_get_jobstate_by_id(client_user1, team1_job_id):
    js = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    ).data
    js_id = js["jobstate"]["id"]

    # get by uuid
    created_js = client_user1.get("/api/v1/jobstates/%s" % js_id)
    assert created_js.status_code == 200
    assert created_js.data["jobstate"]["comment"] == "kikoolol"
    assert created_js.data["jobstate"]["status"] == "running"


def test_get_jobstate_not_found(client_user1):
    result = client_user1.get("/api/v1/jobstates/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobstate_with_embed(client_user1, team1_job_id):
    js = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    ).data
    js_id = js["jobstate"]["id"]

    # verify embed
    js_embed = client_user1.get("/api/v1/jobstates/%s?embed=files,job" % js_id)
    assert js_embed.status_code == 200


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_delete_jobstate_by_id(_, client_user1, team1_job_id):
    js = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    )
    js_id = js.data["jobstate"]["id"]

    url = "/api/v1/jobstates/%s" % js_id

    created_js = client_user1.get(url)
    assert created_js.status_code == 200

    deleted_js = client_user1.delete(url)
    assert deleted_js.status_code == 204

    gjs = client_user1.get(url)
    assert gjs.status_code == 404


# Tests for the isolation


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_create_jobstate_as_user(_, client_user1, team1_job_id):
    jobstate = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    )
    assert jobstate.status_code == 201

    jobstate_id = jobstate.data["jobstate"]["id"]
    jobstate = client_user1.get("/api/v1/jobstates/%s" % jobstate_id)
    assert jobstate.status_code == 200
    assert jobstate.data["jobstate"]["job_id"] == team1_job_id


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_get_jobstate_as_user(_, client_user1, team1_jobstate_id, team1_job_id):
    jobstate = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    ).data
    jobstate_id = jobstate["jobstate"]["id"]
    jobstate = client_user1.get("/api/v1/jobstates/%s" % jobstate_id)
    assert jobstate.status_code == 200


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_delete_jobstate_as_user(_, client_user1, team1_job_id):
    js_user = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    )
    js_user_id = js_user.data["jobstate"]["id"]

    jobstate_delete = client_user1.delete("/api/v1/jobstates/%s" % js_user_id)
    assert jobstate_delete.status_code == 204
