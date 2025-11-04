# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

from dci import auth_mechanism
import flask


def test_hmac_mechanism_api_get_jobs_remoteci(hmac_client_team1):
    jobs_request = hmac_client_team1.get("/api/v1/jobs")
    assert jobs_request.status_code == 200


def test_hmac_mechanism_params(hmac_client_team1):
    jobs_request = hmac_client_team1.get("/api/v1/jobs?embed=components")
    assert jobs_request.status_code == 200


def test_hmac_mechanism_api_get_jobs_feeder(hmac_client_feeder):
    jobs_request = hmac_client_feeder.get("/api/v1/jobs")
    assert jobs_request.status_code == 200


def test_nrt_build_identity_with_remoteci_inactive(
    app,
    session,
    team_admin_id,
    team_redhat_id,
    team_epm_id,
    hmac_client_team1,
    team1_remoteci,
):
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.team_redhat_id = team_redhat_id
        flask.g.team_epm_id = team_epm_id
        flask.g.session = session
        hm = auth_mechanism.HmacMechanism(None)
        bi = hm.build_identity(
            client_info={"client_type": "remoteci", "client_id": team1_remoteci["id"]}
        )
        assert bi is not None
        t = hmac_client_team1.get("/api/v1/remotecis/" + team1_remoteci["id"]).data[
            "remoteci"
        ]
        data = {"state": "inactive"}
        r = hmac_client_team1.put(
            "/api/v1/remotecis/" + team1_remoteci["id"],
            data=data,
            headers={"If-match": t["etag"]},
        )
        assert r.status_code == 200
        assert r.data["remoteci"]["state"] == "inactive"

        bi = hm.build_identity(
            client_info={"client_type": "remoteci", "client_id": team1_remoteci["id"]}
        )
        assert bi is None
