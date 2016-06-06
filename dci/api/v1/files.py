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
import os

import flask
from flask import json
import six

from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import transformations
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models
from dci import dci_config


_TABLE = models.FILES
# associate column names with the corresponding SA Column object
_FILES_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_VALID_EMBED = {
    'jobstate': models.JOBSTATES,
    'jobstate.job': models.JOBS,
    'team': models.TEAMS
}

_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']


# This is the old way to create a files, it assumes the content is provided
# from the jsons POST's data. The content of the file is stored in the FS.
def _old_create_files(user):
    values = schemas.file.post(flask.request.json)

    if values.get('jobstate_id') is None and values.get('job_id') is None:
        raise dci_exc.DCIException('jobstate_id or job_id must be specified',
                                   status_code=400)

    file_id = utils.gen_uuid()
    values.update({
        'id': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'team_id': user['team_id']
    })

    query = _TABLE.insert().values(**values)
    flask.g.db_conn.execute(query)

    # ensure the team's path exist in the FS
    file_path = v1_utils.build_file_path(_FILES_FOLDER, user['team_id'],
                                         file_id)
    with open(file_path, 'w') as f:
        f.write(values['content'])

    result = json.dumps({'file': values})
    return flask.Response(result, 201, content_type='application/json')


# todo(yassine): delete this code when we upgrade the agents
# check if some DCI-* headers are provided, if not call the old
# controller
def use_old_create_files(headers):
    for header, value in six.iteritems(headers):
        if header.lower().startswith('dci'):
            return False
    return True


@api.route('/files', methods=['POST'])
@auth.requires_auth
def create_files(user):
    if use_old_create_files(flask.request.headers):
        return _old_create_files(user)
    else:
        return new_create_files(user)


def new_create_files(user):
    # todo(yassine): use voluptuous for headers validation
    headers_values = v1_utils.flask_headers_to_dict(flask.request.headers)

    values = dict.fromkeys(['md5', 'mime', 'jobstate_id', 'job_id', 'name'])
    values.update(headers_values)

    if values.get('jobstate_id') is None and values.get('job_id') is None:
        raise dci_exc.DCIException('HTTP headers DCI-JOBSTATE-ID or '
                                   'DCI-JOB-ID must be specified')
    if values.get('name') is None:
        raise dci_exc.DCIException('HTTP header DCI-NAME must be specified')

    file_id = utils.gen_uuid()
    # ensure the directory which will contains the file actually exist
    file_path = v1_utils.build_file_path(_FILES_FOLDER, user['team_id'],
                                         file_id)

    with open(file_path, 'wb') as f:
        chunk_size = 4096
        read = flask.request.stream.read
        for chunk in iter(lambda: read(chunk_size) or None, None):
            f.write(chunk)
    file_size = os.path.getsize(file_path)

    values.update({
        'id': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'team_id': user['team_id'],
        'content': None,
        'md5': None,
        'size': file_size
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)
    result = json.dumps({'file': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/files', methods=['GET'])
@auth.requires_auth
def get_all_files(user, j_id=None):
    """Get all files.
    """
    args = schemas.args(flask.request.args.to_dict())

    embed = args['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)

    q_bd.select.extend(select)
    q_bd.join.extend(join)
    q_bd.sort = v1_utils.sort_query(args['sort'], _FILES_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _FILES_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if j_id is not None:
        q_bd.where.append(_TABLE.c.job_id == j_id)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    result = transformations.transform(result)

    return json.jsonify({'files': result, '_meta': {'count': nb_row}})


@api.route('/files/<file_id>', methods=['GET'])
@auth.requires_auth
def get_file_by_id_or_name(user, file_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE)

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)
    q_bd.select.extend(select)
    q_bd.join.extend(join)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    where_clause = sql.or_(_TABLE.c.id == file_id, _TABLE.c.name == file_id)
    q_bd.where.append(where_clause)

    row = flask.g.db_conn.execute(q_bd.build()).fetchone()
    if row is None:
        raise dci_exc.DCINotFound('File', file_id)

    dfile = v1_utils.group_embedded_resources(embed, row)

    result = json.jsonify({'file': dfile})
    return result


@api.route('/files/<file_id>/content', methods=['GET'])
@auth.requires_auth
def get_file_content(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)

    if not (auth.is_admin(user) or auth.is_in_team(user, file['team_id'])):
        raise auth.UNAUTHORIZED

    file_path = v1_utils.build_file_path(_FILES_FOLDER, file['team_id'],
                                         file_id, create=False)

    if not os.path.exists(file_path):
        raise dci_exc.DCIException('Internal server file: not existing',
                                   status_code=404)
    file_size = os.path.getsize(file_path)

    def generate_chunk():
        chunk_size = 1024 ** 2  #  1MB
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size) or None, None):
                yield chunk

    return flask.Response(generate_chunk(), content_type='text/plain',
                          headers={'Content-Length': file_size})


@api.route('/files/<file_id>', methods=['DELETE'])
@auth.requires_auth
def delete_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)

    if not (auth.is_admin(user) or auth.is_in_team(user, file['team_id'])):
        raise auth.UNAUTHORIZED

    where_clause = sql.or_(_TABLE.c.id == file_id, _TABLE.c.name == file_id)
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('File', file_id)

    return flask.Response(None, 204, content_type='application/json')
