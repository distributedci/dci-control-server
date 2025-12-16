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

import flask
import logging
from sqlalchemy import sql

from dci.api.v2 import api
from dci.api.v1 import base
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_and_get_args,
)
from dci.db import declarative
from dci.db import models2


logger = logging.getLogger(__name__)


@api.route("/jobs/<uuid:job_id>/jobstates", methods=["GET"])
@decorators.login_required
def get_jobstates_of_a_job(user, job_id):
    args = check_and_get_args(flask.request.args.to_dict())
    job = base.get_resource_orm(models2.Job, job_id)

    if (
        user.is_not_in_team(job.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    query = flask.g.session.query(models2.Jobstate)
    query = query.filter(models2.Jobstate.job_id == job_id)
    query = declarative.handle_args(query, models2.Jobstate, args)
    nb_jobstates = query.count()
    query = declarative.handle_pagination(query, args)

    jobstates = [js.serialize_v2() for js in query.all()]
    return flask.jsonify(
        {
            "jobstates": jobstates,
            "_meta": {"count": nb_jobstates},
        }
    )


@api.route("/jobs/<uuid:job_id>/files", methods=["GET"])
@decorators.login_required
def get_all_files_from_jobs(user, job_id):
    """Get all files."""
    args = check_and_get_args(flask.request.args.to_dict())
    job = base.get_resource_orm(models2.Job, job_id)
    if (
        user.is_not_in_team(job.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    query = flask.g.session.query(models2.File)
    query = query.filter(
        sql.and_(
            models2.File.job_id == job_id,
            models2.File.state != "archived",
            models2.File.jobstate_id.is_(None),
        )
    )

    query = declarative.handle_args(query, models2.File, args)
    nb_files = query.count()
    query = declarative.handle_pagination(query, args)

    files = [f.serialize() for f in query.all()]

    return flask.jsonify({"files": files, "_meta": {"count": nb_files}})
