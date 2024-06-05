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

import json
import flask
import logging

from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func

from dci import decorators
from dci.api.v1 import api
from dci.db import models2
from dci.common import exceptions as dci_exc, utils

logger = logging.getLogger(__name__)


def insert_or_update_daily_download(
    team_id, component_id, download_amount, download_date
):
    query = (
        insert(models2.DailyDownload)
        .values(
            team_id=team_id,
            component_id=component_id,
            day=download_date,
            total_downloaded=download_amount,
        )
        .on_conflict_do_update(
            index_elements=["team_id", "component_id", "day"],
            set_={
                "total_downloaded": models2.DailyDownload.total_downloaded
                + download_amount
            },
        )
    )
    flask.g.session.execute(query)
    flask.g.session.commit()


def get_from_and_to_dates(args):
    from_param = args.get("from")
    from_date = (
        datetime.strptime(from_param, "%Y-%m-%dT%H:%M:%S") if from_param else None
    )

    to_param = args.get("to")
    to_date = datetime.strptime(to_param, "%Y-%m-%dT%H:%M:%S") if to_param else None
    return from_date, to_date


@api.route("/partner_download_statistics", methods=["GET"])
@decorators.login_required
def get_partner_download_statistics(identity):
    if identity.is_not_super_admin():
        raise dci_exc.Unauthorized()

    query = flask.g.session.query(
        models2.Team.id,
        models2.Team.name,
        func.sum(models2.DailyDownload.total_downloaded).label("total_downloaded"),
    )
    from_date, to_date = get_from_and_to_dates(flask.request.args)
    if from_date:
        query = query.filter(models2.DailyDownload.day >= from_date)
    if to_date:
        query = query.filter(models2.DailyDownload.day <= to_date)

    teams_stats = (
        query.join(
            models2.DailyDownload,
            models2.DailyDownload.team_id == models2.Team.id,
        )
        .group_by(models2.Team.id, models2.Team.name)
        .all()
    )

    download = [
        {
            "team_id": teams_stat.id,
            "team_name": teams_stat.name,
            "total_downloaded": teams_stat.total_downloaded,
        }
        for teams_stat in teams_stats
    ]

    return flask.Response(
        json.dumps({"downloads": download}, cls=utils.JSONEncoder),
        200,
        content_type="application/json",
    )


@api.route("/teams/<uuid:team_id>/download_statistics", methods=["GET"])
@decorators.login_required
def get_download_statistics(identity, team_id):
    if identity.is_not_super_admin():
        raise dci_exc.Unauthorized()

    query = flask.g.session.query(
        models2.Component.id,
        models2.Component.name,
        func.sum(models2.DailyDownload.total_downloaded).label("total_downloaded"),
    )

    from_date, to_date = get_from_and_to_dates(flask.request.args)
    if from_date:
        query = query.filter(models2.DailyDownload.day >= from_date)
    if to_date:
        query = query.filter(models2.DailyDownload.day <= to_date)

    components = (
        query.join(models2.Component)
        .filter(models2.DailyDownload.team_id == team_id)
        .group_by(models2.Component.id)
        .order_by(models2.Component.released_at.desc())
        .all()
    )

    downloads = [
        {
            "id": component.id,
            "name": component.name,
            "total_downloaded": component.total_downloaded,
        }
        for component in components
    ]

    return flask.Response(
        json.dumps({"downloads": downloads}, cls=utils.JSONEncoder),
        200,
        content_type="application/json",
    )
