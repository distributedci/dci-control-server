# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import requests

from dci import dci_config


def test_create_a_task(client_user1, team1_id, team1_job_id, team1_jobstate_id):
    create_task = client_user1.post(
        "/api/v2/tasks",
        data={
            "name": "TASK: [ Print DCI test] **************************************",
            "jobstate_id": team1_jobstate_id,
            "duration": 123,
            "status": "completed",
        },
    )
    assert create_task.status_code == 201
    task = create_task.data["task"]

    upload_url = task["upload_url"]
    content = 'ok: [127.0.0.1] => { "msg": "DCI test" }'

    # Use requests library to make real HTTP PUT to S3 backend
    upload_task_content = requests.put(upload_url, data=content)
    assert upload_task_content.status_code == 200

    task = client_user1.get("/api/v2/tasks/%s" % task["id"]).data["task"]
    assert task["status"] == "completed"
    assert task["duration"] == 123
    assert (
        task["name"] == "TASK: [ Print DCI test] **************************************"
    )
    assert task["jobstate_id"] == team1_jobstate_id
    assert "upload_url" not in task

    get_task_content = client_user1.get("/api/v2/tasks/%s/content" % task["id"])
    assert get_task_content.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    tasks_bucket = dci_config.CONFIG["STORE_TASKS_CONTAINER"]
    expected_location = (
        f"{s3_endpoint_url}/{tasks_bucket}/{team1_id}/{team1_job_id}/{task['id']}"
    )
    assert get_task_content.headers["Location"].startswith(expected_location)
