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
import logging

from dci.api.v1 import api
from dci.api.v1 import base
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models2


logger = logging.getLogger(__name__)


@api.route("/jobs/<uuid:job_id>/kv", methods=["POST"])
@decorators.login_required
def add_kv_to_job(user, job_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = flask.request.json

    job = base.get_resource_orm(models2.Job, job_id, if_match_etag)

    if user.is_not_in_team(job.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values["job_id"] = job_id
    jkv = base.create_resource_orm(models2.JobKeyValue, values)

    return flask.Response(
        json.dumps({"kv": jkv}),
        201,
        content_type="application/json",
    )
