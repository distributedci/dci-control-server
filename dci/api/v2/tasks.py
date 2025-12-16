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

import flask
from flask import json

from dci.api.v2 import api
from dci.api.v1 import base
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import check_json_is_valid, task_schema
from dci.api.v1 import utils
from dci.db import models2


def build_task_file_path(team_id, job_id, task_id):
    root = str(team_id)
    middle = str(job_id)
    task_id = str(task_id)
    return "%s/%s/%s" % (root, middle, task_id)


@api.route("/tasks", methods=["POST"])
@decorators.login_required
def create_task(user):
    values = flask.request.json
    check_json_is_valid(task_schema, values)
    values.update(utils.common_values_dict())

    jobstate_id = values.get("jobstate_id")
    jobstate = base.get_resource_orm(models2.Jobstate, jobstate_id)
    job = base.get_resource_orm(models2.Job, jobstate.job_id)

    if user.is_not_in_team(job.team_id):
        raise dci_exc.Unauthorized()

    created_task = base.create_resource_orm(models2.Task, values)
    file_path = build_task_file_path(job.team_id, job.id, created_task["id"])
    upload_url = flask.g.store.get_presigned_url("put_object", "tasks", file_path)

    created_task["upload_url"] = upload_url

    result = {"task": created_task}
    return flask.Response(json.dumps(result), 201, content_type="application/json")


@api.route("/tasks/<uuid:task_id>", methods=["GET"])
@decorators.login_required
def get_task_by_id(user, task_id):
    task = base.get_resource_orm(models2.Task, task_id)
    jobstate = base.get_resource_orm(models2.Jobstate, task.jobstate_id)
    job = base.get_resource_orm(models2.Job, jobstate.job_id)

    if (
        user.is_not_in_team(job.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    return flask.Response(
        json.dumps({"task": task.serialize()}),
        200,
        content_type="application/json",
    )


@api.route("/tasks/<uuid:task_id>/content", methods=["GET", "HEAD"])
@decorators.login_required
def get_task_content(user, task_id):
    task = base.get_resource_orm(models2.Task, task_id)
    jobstate = base.get_resource_orm(models2.Jobstate, task.jobstate_id)
    job = base.get_resource_orm(models2.Job, jobstate.job_id)

    if (
        user.is_not_in_team(job.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    file_path = build_task_file_path(job.team_id, job.id, task.id)

    presign_url_method = "get_object"
    if flask.request.method == "HEAD":
        presign_url_method = "head_object"

    presigned_url = flask.g.store.get_presigned_url(
        presign_url_method, "tasks", file_path
    )

    return flask.Response(
        None, 302, content_type="application/json", headers={"Location": presigned_url}
    )
