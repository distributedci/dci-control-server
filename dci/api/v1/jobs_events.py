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

import flask
from flask import json
from sqlalchemy import select, func, delete

from dci.api.v1 import base
from dci.api.v1 import api
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    clean_json_with_schema,
    counter_schema,
    check_and_get_args,
)
from dci.common import utils
from dci.db import models2
from dci.db import declarative


@api.route("/jobs_events/<int:sequence>", methods=["GET"])
@decorators.login_required
def get_jobs_events_from_sequence(user, sequence):
    """Get all the jobs events from a given sequence number."""

    args = check_and_get_args(flask.request.args.to_dict())

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    query = (
        select(models2.JobEvent)
        .select_from(models2.JobEvent)
        .join(models2.Job, models2.Job.id == models2.JobEvent.job_id)
        .where(models2.JobEvent.id >= sequence)
    )

    query = declarative.handle_args(query, models2.JobEvent, args)
    count_query = select(func.count()).select_from(query.subquery())
    nb_jobs_events = flask.g.session.execute(count_query).scalar()

    query = declarative.handle_pagination(query, args)
    jobs_events = [
        je.serialize() for je in flask.g.session.execute(query).scalars().all()
    ]

    return json.jsonify(
        {"jobs_events": jobs_events, "_meta": {"count": nb_jobs_events}}
    )


@api.route("/jobs_events/<int:sequence>", methods=["DELETE"])
@decorators.login_required
def purge_jobs_events_from_sequence(user, sequence):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()
    try:
        query = delete(models2.JobEvent).where(models2.JobEvent.id >= sequence)
        flask.g.session.execute(query)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)
    return flask.Response(None, 204, content_type="application/json")


def create_event(job_id, status, topic_id=None):
    values = {"job_id": str(job_id), "status": status, "topic_id": str(topic_id)}
    if not topic_id:
        job = base.get_resource_orm(models2.Job, job_id)
        values["topic_id"] = str(job.topic_id)

    base.create_resource_orm(models2.JobEvent, values)


@api.route("/jobs_events/sequence", methods=["GET"])
@decorators.login_required
def get_current_sequence(user):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    def create_sequence():
        etag = utils.gen_etag()
        base.create_resource_orm(
            models2.Counter, {"name": "jobs_events", "sequence": 0, "etag": etag}
        )

    def get_sequence():
        query = select(models2.Counter).where(models2.Counter.name == "jobs_events")
        return flask.g.session.execute(query).scalar()

    je_sequence = get_sequence()
    if not je_sequence:
        create_sequence()
        je_sequence = get_sequence()

    return json.jsonify(
        {"sequence": {"sequence": je_sequence.sequence, "etag": je_sequence.etag}}
    )


@api.route("/jobs_events/sequence", methods=["PUT"])
@decorators.login_required
def put_current_sequence(user):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(counter_schema, flask.request.json)
    query = select(models2.Counter).where(
        models2.Counter.name == "jobs_events",
        models2.Counter.etag == if_match_etag,
    )
    counter = flask.g.session.execute(query).scalar()
    if not counter:
        raise dci_exc.DCIConflict("jobs_events", "sequence")
    counter.sequence = values["sequence"]
    flask.g.session.commit()
    return flask.Response(None, 204, content_type="application/json")
