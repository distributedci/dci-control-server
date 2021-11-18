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
import requests

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import export_control
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    analytics_task_duration_cumulated,
    check_json_is_valid
)
from dci.dci_config import CONFIG
from dci.db import models2
from dci import decorators


@api.route('/analytics/tasks_duration_cumulated', methods=['GET'])
@decorators.login_required
def tasks_duration_cumulated(user):
    args = flask.request.args.to_dict()
    check_json_is_valid(analytics_task_duration_cumulated, args)
    topic = base.get_resource_orm(models2.Topic, args['topic_id'])
    remoteci = base.get_resource_orm(models2.Remoteci, args['remoteci_id'])

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        if remoteci.team_id not in user.teams_id:
            raise dci_exc.Unauthorized()
    export_control.verify_access_to_topic(user, topic)

    query = {
        "query": {
            "dis_max": {
                "queries": [
                    {"match": {"topic_id": args['topic_id']}},
                    {"match": {"remoteci_id": args['remoteci_id']}}
                ],
            }
        }
    }
    res = requests.get("%s/tasks_duration_cumulated/_search" % CONFIG['ELASTICSEARCH_URL'], json=query)
    if res.status_code == 200:
        return flask.jsonify(res.json()['hits'])
    else:
        return flask.Response({"error: %s" % res.text: "error: %s" % res.status_code}, 400, content_type='application/json')
