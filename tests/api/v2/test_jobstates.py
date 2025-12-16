# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Red Hat, Inc
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


def test_get_jobstate_return_files_and_tasks_with_tasks_key(
    client_user1, team1_jobstate_id, team1_jobstate_file_id, team1_jobstate_task_id
):
    get_jobstate = client_user1.get(f"/api/v2/jobstates/{team1_jobstate_id}")
    assert get_jobstate.status_code == 200
    jobstate = get_jobstate.data["jobstate"]
    assert jobstate["id"] == team1_jobstate_id
    assert "tasks" in jobstate
    assert "files" not in jobstate
    tasks = jobstate["tasks"]
    assert len(tasks) == 2
    for task in tasks:
        assert task["id"] in [team1_jobstate_file_id, team1_jobstate_task_id]


def test_cant_access_other_jobstate(client_user2, team1_jobstate_id):
    get_jobstate = client_user2.get(f"/api/v2/jobstates/{team1_jobstate_id}")
    assert get_jobstate.status_code == 401
