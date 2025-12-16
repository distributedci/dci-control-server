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

import flask
from flask import json

from dci.api.v2 import api
from dci.api.v1 import base
from dci import decorators
from dci.common.exceptions import Unauthorized

from dci.db import models2


@api.route("/jobstates/<uuid:js_id>", methods=["GET"])
@decorators.login_required
def get_jobstate_by_id(user, js_id):
    jobstate = base.get_resource_orm(models2.Jobstate, js_id)
    job = base.get_resource_orm(models2.Job, jobstate.job_id)

    if (
        user.is_not_in_team(job.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise Unauthorized()

    return flask.Response(
        json.dumps({"jobstate": jobstate.serialize_v2()}),
        200,
        content_type="application/json",
    )
