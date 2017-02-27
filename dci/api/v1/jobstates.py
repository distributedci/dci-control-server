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

import flask
from flask import json

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.JOBSTATES
_VALID_EMBED = embeds.jobstates()
_JS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE, _VALID_EMBED)


def insert_jobstate(user, values, created_at=None):
    values.update({
        'id': utils.gen_uuid(),
        'created_at': created_at or datetime.datetime.utcnow().isoformat(),
        'team_id': user['team_id']
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)


@api.route('/jobstates', methods=['POST'])
@auth.requires_auth
def create_jobstates(user):
    created_at, _ = utils.get_dates(user)
    values = schemas.jobstate.post(flask.request.json)

    insert_jobstate(user, values, created_at)

    # Update job status
    job_id = values.get('job_id')

    query_update_job = (models.JOBS.update()
                        .where(models.JOBS.c.id == job_id)
                        .values(status=values.get('status')))

    result = flask.g.db_conn.execute(query_update_job)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Job', job_id)

    result = json.dumps({'jobstate': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/jobstates', methods=['GET'])
@auth.requires_auth
def get_all_jobstates(user, j_id=None):
    """Get all jobstates.
    """
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, args['limit'], args['offset'],
                                 _VALID_EMBED)
    q_bd.join(embed)

    q_bd.sort = v1_utils.sort_query(args['sort'], _JS_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _JS_COLUMNS)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    # used for counting the number of rows when j_id is not None
    if j_id is not None:
        q_bd.where.append(_TABLE.c.job_id == j_id)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'jobstates': rows, '_meta': {'count': nb_row}})


@api.route('/jobstates/<uuid:js_id>', methods=['GET'])
@auth.requires_auth
def get_jobstate_by_id(user, js_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(_TABLE.c.id == js_id)

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Jobstate', js_id)
    jobstate = rows[0]

    res = flask.jsonify({'jobstate': jobstate})
    return res


@api.route('/jobstates/<uuid:js_id>', methods=['DELETE'])
@auth.requires_auth
def delete_jobstate_by_id(user, js_id):
    jobstate = v1_utils.verify_existence_and_get(js_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, jobstate['team_id'])):
        raise auth.UNAUTHORIZED

    where_clause = _TABLE.c.id == js_id
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Jobstate', js_id)

    return flask.Response(None, 204, content_type='application/json')
