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

from dci.worker import access_data_layer as a_d_l


def test_get_emails_from_remoteci(client_user1, team1_remoteci_id, app, session):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)
    assert r.status_code == 201

    with app.app_context():
        emails = a_d_l.get_emails_from_remoteci(session, team1_remoteci_id)
        assert emails == ["user1@example.org"]


def test_get_emails_from_remoteci_deleted(
    client_user1, team1_remoteci_id, app, session
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)
    assert r.status_code == 201
    r = client_user1.get("/api/v1/remotecis/%s" % team1_remoteci_id)
    r = client_user1.delete(
        "/api/v1/remotecis/%s" % team1_remoteci_id,
        headers={"If-match": r.data["remoteci"]["etag"]},
    )
    assert r.status_code == 204

    with app.app_context():
        emails = a_d_l.get_emails_from_remoteci(session, team1_remoteci_id)
        assert emails == []


def test_get_serialized_component(session, rhel_80_component_id):
    component = a_d_l.get_serialized_component(session, rhel_80_component_id)
    assert "id" in component
    assert component["id"] == rhel_80_component_id
    assert "topic" in component
    assert "name" in component
    assert "state" in component
    assert "topic_id" in component


def test_get_serialized_job(session, team1_job_id):
    job = a_d_l.get_serialized_job(session, team1_job_id)
    assert "id" in job
    assert job["id"] == team1_job_id
    assert "topic" in job
    assert "remoteci" in job
    assert "status" in job
    assert "results" in job
    assert "components" in job
    assert "remoteci_id" in job
    assert "topic_id" in job
