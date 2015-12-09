# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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
import sqlalchemy.sql

from dci.server.api.v1 import api
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth
from dci.server.common import exceptions as dci_exc
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models

# associate column names with the corresponding SA Column object
_C_COLUMNS = v1_utils.get_columns_name_with_objects(models.COMPONENTS)
_VALID_EMBED = {'componenttype': models.COMPONENTYPES}


def _verify_existence_and_get_c(c_id):
    return v1_utils.verify_existence_and_get(
        [models.COMPONENTS], c_id,
        sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                           models.COMPONENTS.c.name == c_id))


@api.route('/components', methods=['POST'])
@auth.requires_auth()
def create_components(user_info):
    etag = utils.gen_etag()
    values = schemas.component.post(flask.request.json)
    values.update({'id': utils.gen_uuid(),
                   'created_at': datetime.datetime.utcnow().isoformat(),
                   'updated_at': datetime.datetime.utcnow().isoformat(),
                   'etag': etag})

    query = models.COMPONENTS.insert().values(**values)

    flask.g.db_conn.execute(query)

    result = json.dumps({'component': values})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/components', methods=['GET'])
@auth.requires_auth()
def get_all_components(user_info, ct_id=None):
    """Get all components.

    If ct_id is not None, then return all the components with a type
    pointed by ct_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())

    v1_utils.verify_embed_list(args['embed'], _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.COMPONENTS])

    # if embed then construct the query with a join
    if args['embed']:
        query = v1_utils.get_query_with_join(models.COMPONENTS,
                                             [models.COMPONENTS],
                                             args['embed'], _VALID_EMBED)

    query = v1_utils.sort_query(query, args['sort'], _C_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.COMPONENTS,
                                 _C_COLUMNS)

    # used for counting the number of rows when ct_id is not None
    where_ct_cond = None
    if ct_id is not None:
        where_ct_cond = models.COMPONENTS.c.componenttype_id == ct_id
        query = query.where(where_ct_cond)

    # adds the limit/offset parameters
    if args['limit'] is not None:
        query = query.limit(args['limit'])

    if args['offset'] is not None:
        query = query.offset(args['offset'])

    # get the number of rows for the '_meta' section
    nb_cts = utils.get_number_of_rows(models.COMPONENTS, where_ct_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(args['embed'], row)
              for row in rows]

    result = {'components': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/components/<c_id>', methods=['GET'])
@auth.requires_auth()
def get_component_by_id_or_name(user_info, c_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.COMPONENTS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.COMPONENTS,
                                             [models.COMPONENTS], embed,
                                             _VALID_EMBED)

    query = query.where(sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                                           models.COMPONENTS.c.name == c_id))

    row = flask.g.db_conn.execute(query).fetchone()
    component = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCIException("component '%s' not found." % c_id,
                                   status_code=404)

    etag = component['etag']
    component = {'component': component}
    component = json.dumps(component, default=utils.json_encoder)
    return flask.Response(component, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/components/<c_id>', methods=['DELETE'])
@auth.requires_auth()
def delete_component_by_id_or_name(user_info, c_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_c(c_id)

    query = models.COMPONENTS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                               models.COMPONENTS.c.name == c_id),
            models.COMPONENTS.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Component '%s' already deleted or "
                                   "etag not matched." % c_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
