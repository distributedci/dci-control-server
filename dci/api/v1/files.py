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
from dci.api.v1 import base
from dci.api.v1 import transformations as tsfm
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models
from dci import dci_config


_TABLE = models.FILES
# associate column names with the corresponding SA Column object
_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']
_VALID_EMBED = embeds.files()
_FILES_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'jobstate': False,
    'jobstate.job': False,
    'job': False,
    'team': False
}


@api.route('/files', methods=['POST'])
@auth.login_required
def create_files(user):
    # todo(yassine): use voluptuous for headers validation
    headers_values = v1_utils.flask_headers_to_dict(flask.request.headers)
    swift = dci_config.get_store('files')

    values = dict.fromkeys(['md5', 'mime', 'jobstate_id',
                            'job_id', 'name', 'test_id'])
    values.update(headers_values)

    if values.get('jobstate_id') is None and values.get('job_id') is None:
        raise dci_exc.DCIException('HTTP headers DCI-JOBSTATE-ID or '
                                   'DCI-JOB-ID must be specified')
    if values.get('name') is None:
        raise dci_exc.DCIException('HTTP header DCI-NAME must be specified')

    if values['jobstate_id']:
        query = v1_utils.QueryBuilder(models.JOBSTATES)
        query.add_extra_condition(
            models.JOBSTATES.c.id == values['jobstate_id'])
        row = query.execute(fetchone=True)
        if row is None:
            raise dci_exc.DCINotFound('Jobstate', values['jobstate_id'])
        values['job_id'] = row['jobstates_job_id']

    query = v1_utils.QueryBuilder(models.JOBS)
    if not auth.is_admin(user):
        query.add_extra_condition(models.JOBS.c.team_id == user['team_id'])
    query.add_extra_condition(models.JOBS.c.id == values['job_id'])
    row = query.execute(fetchone=True)
    if row is None:
        raise dci_exc.DCINotFound('Job', values['job_id'])

    file_id = utils.gen_uuid()
    # ensure the directory which will contains the file actually exist

    file_path = swift.build_file_path(user['team_id'],
                                      values['job_id'],
                                      file_id)

    swift.upload(file_path, flask.request.stream)
    s_file = swift.head(file_path)

    etag = utils.gen_etag()
    values.update({
        'id': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'team_id': user['team_id'],
        'md5': None,
        'size': s_file['content-length'],
        'state': 'active',
        'etag': etag,
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)
    result = json.dumps({'file': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/files', methods=['GET'])
@auth.login_required
def get_all_files(user, j_id=None):
    """Get all files.
    """
    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _FILES_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])
    if j_id is not None:
        query.add_extra_condition(_TABLE.c.job_id == j_id)
    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)
    return json.jsonify({'files': rows, '_meta': {'count': nb_rows}})


@api.route('/files/<uuid:file_id>', methods=['GET'])
@auth.login_required
def get_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)
    return base.get_resource_by_id(user, file, _TABLE, _EMBED_MANY)


@api.route('/files/<uuid:file_id>/content', methods=['GET'])
@auth.login_required
def get_file_content(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)
    swift = dci_config.get_store('files')

    def get_object(swift_object):
        for block in swift.get(swift_object)[1]:
            yield block

    if not (auth.is_admin(user) or auth.is_in_team(user, file['team_id'])):
        raise auth.UNAUTHORIZED

    file_path = swift.build_file_path(file['team_id'],
                                      file['job_id'],
                                      file_id)

    # Check if file exist on the storage engine
    swift.head(file_path)

    if flask.request.is_xhr and file['mime'] == 'application/junit':
        data = ''.join(swift.get(file_path)[1])
        data = tsfm.junit2json(data)
        headers = {
            'Content-Length': len(data),
            'Content-Disposition': 'attachment; filename=%s' %
                                   file['name'].replace(' ', '_')
        }
        return flask.Response(
            data,
            content_type=file['mime'],
            headers=headers
        )
    else:
        headers = {
            'Content-Length': file['size'],
            'Content-Disposition': 'attachment; filename=%s' %
                                   file['name'].replace(' ', '_')
        }
        return flask.Response(
            get_object(file_path),
            content_type=file['mime'] or 'text/plain',
            headers=headers
        )


@api.route('/files/<uuid:file_id>', methods=['DELETE'])
@auth.login_required
def delete_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)

    if not (auth.is_admin(user) or auth.is_in_team(user, file['team_id'])):
        raise auth.UNAUTHORIZED

    values = {'state': 'archived'}
    where_clause = _TABLE.c.id == file_id

    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('File', file_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/files/purge', methods=['GET'])
@auth.login_required
def get_to_purge_archived_files(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/files/purge', methods=['POST'])
@auth.login_required
def purge_archived_files(user):
    return base.purge_archived_resources(user, _TABLE)
