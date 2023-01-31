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


def test_add_get(remoteci_context, job_user_id):
    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == {}

    data_init = {"k1": "v1", "k2": "v2"}
    r = remoteci_context.post(
        "/api/v1/jobs/%s/keys_values" % job_user_id, data=data_init
    )
    assert r.status_code == 201

    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == data_init

    data_new_key = {"k3": "v3"}
    r = remoteci_context.post(
        "/api/v1/jobs/%s/keys_values" % job_user_id, data=data_new_key
    )
    assert r.status_code == 201

    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == data_new_key


def test_update(remoteci_context, job_user_id):
    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == {}

    data = {"k2": "v2"}
    r = remoteci_context.put("/api/v1/jobs/%s/keys_values" % job_user_id, data=data)
    assert r.status_code == 204

    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == data

    data = {"k1": "v1"}
    r = remoteci_context.put("/api/v1/jobs/%s/keys_values" % job_user_id, data=data)
    assert r.status_code == 204

    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == {"k1": "v1", "k2": "v2"}

    data = {"k1": "v2"}
    r = remoteci_context.put("/api/v1/jobs/%s/keys_values" % job_user_id, data=data)
    assert r.status_code == 204

    j = remoteci_context.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert j["keys_values"] == {"k1": "v2", "k2": "v2"}
