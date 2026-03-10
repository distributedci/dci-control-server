# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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
import mock


@mock.patch("dci.app.dci_kombu.KombuProducer")
def test_get_stats(
    _,
    client_admin,
    team_admin_job,
    client_user1,
    team1_job,
    rhel_80_topic,
    rhel_product,
):
    client_admin.post(
        "/api/v1/jobstates", data={"job_id": team_admin_job["id"], "status": "failure"}
    )
    client_user1.post(
        "/api/v1/jobstates", data={"job_id": team1_job["id"], "status": "success"}
    )
    assert client_admin.get("/api/v1/stats").data["stats"] == [
        {
            "jobs": [
                {
                    "created_at": team1_job["created_at"],
                    "id": team1_job["id"],
                    "remoteci_name": "user remoteci",
                    "status": "success",
                    "team_name": "team1",
                },
                {
                    "created_at": team_admin_job["created_at"],
                    "id": team_admin_job["id"],
                    "remoteci_name": "admin remoteci",
                    "status": "failure",
                    "team_name": "admin",
                },
            ],
            "nbOfJobs": 2,
            "nbOfSuccessfulJobs": 1,
            "percentageOfSuccess": 50,
            "product": {"id": rhel_product["id"], "name": rhel_product["name"]},
            "topic": {"id": rhel_80_topic["id"], "name": "RHEL-8.0"},
        }
    ]
    assert client_user1.get("/api/v1/stats").data["stats"] == [
        {
            "jobs": [
                {
                    "created_at": team1_job["created_at"],
                    "id": team1_job["id"],
                    "remoteci_name": "user remoteci",
                    "status": "success",
                    "team_name": "team1",
                }
            ],
            "nbOfJobs": 1,
            "nbOfSuccessfulJobs": 1,
            "percentageOfSuccess": 100,
            "product": {"id": rhel_product["id"], "name": rhel_product["name"]},
            "topic": {"id": rhel_80_topic["id"], "name": "RHEL-8.0"},
        }
    ]
