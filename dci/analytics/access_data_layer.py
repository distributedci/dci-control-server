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

from datetime import timedelta
import sqlalchemy.orm as sa_orm
from sqlalchemy import select

from dci.db import models2
from dci.common.time import get_utc_now


def get_jobs(session, offset, limit, unit, amount, status=None):
    delta = {unit: amount}
    query = select(models2.Job)
    if status:
        query = query.where(models2.Job.status == status)
    query = (
        query.where(models2.Job.state != "archived")
        .where(models2.Job.updated_at >= (get_utc_now() - timedelta(**delta)))
        .order_by(models2.Job.updated_at.asc())
        .offset(offset)
        .limit(limit)
        .options(
            sa_orm.selectinload(models2.Job.components).defer(models2.Component.data)
        )
        .options(
            sa_orm.selectinload(models2.Job.jobstates).selectinload(
                models2.Jobstate.files
            )
        )
        .options(sa_orm.selectinload(models2.Job.files))
        .options(sa_orm.selectinload(models2.Job.results))
        .options(sa_orm.joinedload(models2.Job.pipeline, innerjoin=False))
        .options(sa_orm.joinedload(models2.Job.remoteci, innerjoin=True))
        .options(sa_orm.joinedload(models2.Job.topic, innerjoin=True))
        .options(sa_orm.joinedload(models2.Job.product, innerjoin=True))
        .options(sa_orm.joinedload(models2.Job.team, innerjoin=True))
        .options(sa_orm.joinedload(models2.Job.keys_values, innerjoin=False))
    )

    jobs = [
        j.serialize(ignore_columns=["data", "topic.data"])
        for j in session.execute(query).unique().scalars().all()
    ]

    return jobs


def get_job_by_id(session, job_id):
    query = select(models2.Job)
    query = query.where(models2.Job.id == job_id)

    query = (
        query.options(
            sa_orm.selectinload(models2.Job.components).defer(models2.Component.data)
        )
        .options(
            sa_orm.selectinload(models2.Job.jobstates).selectinload(
                models2.Jobstate.files
            )
        )
        .options(sa_orm.selectinload(models2.Job.files))
        .options(sa_orm.selectinload(models2.Job.results))
        .options(sa_orm.joinedload(models2.Job.pipeline, innerjoin=False))
        .options(sa_orm.joinedload(models2.Job.remoteci, innerjoin=True))
        .options(
            sa_orm.joinedload(models2.Job.topic, innerjoin=True).defer(
                models2.Topic.data
            )
        )
        .options(sa_orm.joinedload(models2.Job.product, innerjoin=True))
        .options(sa_orm.joinedload(models2.Job.team, innerjoin=True))
        .options(sa_orm.joinedload(models2.Job.keys_values, innerjoin=False))
        .options(sa_orm.defer(models2.Job.data))
    )

    return session.execute(query).unique().scalar_one().serialize()


def get_components(session, offset, limit, unit, amount):
    delta = {unit: amount}

    query = (
        select(models2.Component)
        .where(models2.Component.state != "archived")
        .where(models2.Component.created_at >= (get_utc_now() - timedelta(**delta)))
        .order_by(models2.Component.created_at.asc())
        .options(sa_orm.selectinload(models2.Component.jobs))
        .options(sa_orm.defer(models2.Component.data))
        .offset(offset)
        .limit(limit)
    )

    jobs = [c.serialize() for c in session.execute(query).scalars().all()]

    return jobs
