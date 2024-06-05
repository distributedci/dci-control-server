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

import datetime
import json
import flask
import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func

from dci import decorators
from dci.api.v1 import api
from dci.db import models2
from dci.common import exceptions as dci_exc, utils

logger = logging.getLogger(__name__)


def insert_or_update_daily_download(
    remoteci_id, component_id, download_amount, download_date
):
    query = (
        insert(models2.DailyDownload)
        .values(
            remoteci_id=remoteci_id,
            component_id=component_id,
            day=download_date,
            total_downloaded=download_amount,
        )
        .on_conflict_do_update(
            index_elements=["remoteci_id", "component_id", "day"],
            set_={
                "total_downloaded": models2.DailyDownload.total_downloaded
                + download_amount
            },
        )
    )
    flask.g.session.execute(query)
    flask.g.session.commit()


@api.route("/partner_download_statistics", methods=["GET"])
@decorators.login_required
def get_partner_download_statistics(user):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    since = datetime.datetime.now() - datetime.timedelta(30)

    teams_stats = (
        flask.g.session.query(
            models2.Team.id,
            models2.Team.name,
            func.sum(models2.DailyDownload.total_downloaded).label("total_downloaded"),
        )
        .join(models2.Remoteci, models2.Remoteci.team_id == models2.Team.id)
        .join(
            models2.DailyDownload,
            models2.DailyDownload.remoteci_id == models2.Remoteci.id,
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
