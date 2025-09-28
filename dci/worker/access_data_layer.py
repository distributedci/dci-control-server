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


from sqlalchemy import orm as sa_orm

from dci.common import exceptions as dci_exc
from dci.db import models2


def get_resource_orm(session, table, id, etag=None, options=None):
    try:
        query = session.query(table).filter(table.id == id)
        try:
            getattr(table, "state")
            query = query.filter(table.state != "archived")
        except AttributeError:
            pass

        if etag:
            query = query.filter(table.etag == etag)
        if options:
            query = query.options(*options)
        return query.one()
    except sa_orm.exc.NoResultFound:
        resource_name = table.__tablename__[:-1]
        raise dci_exc.DCIException(
            message="%s not found" % resource_name, status_code=404
        )


def get_emails_subscribed_to_topic(session, topic_id):
    try:
        query = (
            session.query(models2.User.email)
            .join(models2.UserTopic)
            .filter(models2.UserTopic.topic_id == topic_id)
        )
        return [um[0] for um in query.all()]
    except dci_exc.DCIException:
        return []


def get_emails_from_remoteci(session, remoteci_id):
    try:
        remoteci = get_resource_orm(session, models2.Remoteci, remoteci_id)
        return [u.email for u in remoteci.users]
    except dci_exc.DCIException:
        return []


def get_serialized_job(session, job_id):
    job = get_resource_orm(
        session,
        models2.Job,
        job_id,
        options=[
            sa_orm.joinedload("topic", innerjoin=True),
            sa_orm.joinedload("remoteci", innerjoin=True),
            sa_orm.selectinload("components"),
            sa_orm.selectinload("results"),
        ],
    )
    return job.serialize()


def get_serialized_component(session, component_id):
    component = get_resource_orm(
        session,
        models2.Component,
        component_id,
        options=[
            sa_orm.joinedload("topic", innerjoin=True),
        ],
    )
    return component.serialize()
