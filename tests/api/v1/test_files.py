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

from __future__ import unicode_literals
import pytest
import six

from dci.api.v1 import utils as v1_utils
from dci import dci_config

import os


_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']


def test_create_files(admin, jobstate_id, team_admin_id):
    file = admin.post('/api/v1/files',
                      headers={'DCI-JOBSTATE-ID': jobstate_id,
                               'DCI-NAME': 'kikoolol'},
                      data="content").data
    file_id = file['file']['id']
    file = admin.get('/api/v1/files/%s' % file_id).data
    assert file['file']['name'] == 'kikoolol'

    file_directory_path = v1_utils.build_file_directory_path(
        _FILES_FOLDER, team_admin_id, file_id)
    file_path = '%s/%s' % (file_directory_path, file_id)
    assert os.path.exists(file_path)
    with open(file_path, "r") as f:
        assert f.read()[1:-1] == 'content'


def test_old_create_files(admin, jobstate_id, team_admin_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'content': 'content',
                            'name': 'kikoolol'}).data
    file_id = file['file']['id']
    file = admin.get('/api/v1/files/%s' % file_id).data
    assert file['file']['name'] == 'kikoolol'

    file_directory_path = v1_utils.build_file_directory_path(
        _FILES_FOLDER, team_admin_id, file_id)
    file_path = '%s/%s' % (file_directory_path, file_id)
    assert os.path.exists(file_path)
    with open(file_path, "r") as f:
        assert f.read() == "content"


def test_get_all_files(admin, jobstate_id):
    file_1 = admin.post('/api/v1/files',
                        headers={'DCI-JOBSTATE-ID': jobstate_id,
                                 'DCI-NAME': 'kikoolol1'}).data
    file_1_id = file_1['file']['id']

    file_2_2 = admin.post('/api/v1/files',
                          headers={'DCI-JOBSTATE-ID': jobstate_id,
                                   'DCI-NAME': 'kikoolol2'}).data
    file_2_id = file_2_2['file']['id']

    db_all_files = admin.get('/api/v1/files?sort=created_at').data
    db_all_files = db_all_files['files']
    db_all_files_ids = [file['id'] for file in db_all_files]

    assert db_all_files_ids == [file_1_id, file_2_id]


def test_get_all_files_with_pagination(admin, jobstate_id):
    # create 4 files types and check meta count
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol1'}
    admin.post('/api/v1/files', headers=headers)
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol2'}
    admin.post('/api/v1/files', headers=headers)
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol3'}
    admin.post('/api/v1/files', headers=headers)
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol4'}
    admin.post('/api/v1/files', headers=headers)

    # check meta count
    files = admin.get('/api/v1/files').data
    assert files['_meta']['count'] == 4

    # verify limit and offset are working well
    files = admin.get('/api/v1/files?limit=2&offset=0').data
    assert len(files['files']) == 2

    files = admin.get('/api/v1/files?limit=2&offset=2').data
    assert len(files['files']) == 2

    # if offset is out of bound, the api returns an empty list
    files = admin.get('/api/v1/files?limit=5&offset=300')
    assert files.status_code == 200
    assert files.data['files'] == []


def test_get_all_files_with_embed(admin, jobstate_id, team_admin_id, job_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol1'}
    admin.post('/api/v1/files', headers=headers)
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol2'}
    admin.post('/api/v1/files', headers=headers)

    # verify embed
    files = admin.get('/api/v1/files?embed=team,jobstate,jobstate.job').data

    for file in files['files']:
        assert 'team_id' not in file
        assert 'team' in file
        assert file['team']['id'] == team_admin_id
        assert 'jobstate_id' not in file
        assert 'jobstate' in file
        assert file['jobstate']['id'] == jobstate_id
        assert file['jobstate']['job']['id'] == job_id


def test_get_all_files_with_where(admin, jobstate_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'lol1'}
    file = admin.post('/api/v1/files', headers=headers).data
    file_id = file['file']['id']

    db_job = admin.get('/api/v1/files?where=id:%s' % file_id).data
    db_job_id = db_job['files'][0]['id']
    assert db_job_id == file_id

    db_job = admin.get('/api/v1/files?where=name:lol1').data
    db_job_id = db_job['files'][0]['id']
    assert db_job_id == file_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/files?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_files_with_sort(admin, jobstate_id):
    # create 4 files ordered by created time
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'a'}
    file_1_1_id = admin.post('/api/v1/files',
                             headers=headers).data['file']['id']
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'a'}
    file_1_2_id = admin.post('/api/v1/files',
                             headers=headers).data['file']['id']
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'b'}
    file_2_1_id = admin.post('/api/v1/files',
                             headers=headers).data['file']['id']
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'b'}
    file_2_2_id = admin.post('/api/v1/files',
                             headers=headers).data['file']['id']

    files = admin.get('/api/v1/files?sort=created_at').data
    files_ids = [file['id'] for file in files['files']]
    assert files_ids == [file_1_1_id, file_1_2_id, file_2_1_id, file_2_2_id]

    # sort by name first and then reverse by created_at
    files = admin.get('/api/v1/files?sort=name,-created_at').data
    files_ids = [file['id'] for file in files['files']]
    assert files_ids == [file_1_2_id, file_1_1_id, file_2_2_id, file_2_1_id]


def test_get_file_by_id_or_name(admin, jobstate_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'kikoolol'}
    file = admin.post('/api/v1/files',
                      headers=headers).data
    file_id = file['file']['id']

    # get by uuid
    created_file = admin.get('/api/v1/files/%s' % file_id)
    assert created_file.status_code == 200
    assert created_file.data['file']['name'] == 'kikoolol'

    # get by name
    created_file = admin.get('/api/v1/files/kikoolol')
    assert created_file.status_code == 200
    assert created_file.data['file']['name'] == 'kikoolol'


def test_get_file_not_found(admin):
    result = admin.get('/api/v1/files/ptdr')
    assert result.status_code == 404


def test_get_file_with_embed(admin, jobstate_id, team_admin_id):
    pt = admin.get('/api/v1/teams/%s' % team_admin_id).data
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'kikoolol'}
    file = admin.post('/api/v1/files', headers=headers).data

    file_id = file['file']['id']
    del file['file']['team_id']
    file['file']['team'] = pt['team']

    # verify embed
    file_embed = admin.get('/api/v1/files/%s?embed=team' % file_id).data
    assert file == file_embed


def test_get_jobdefinition_with_embed_not_valid(admin):
    file = admin.get('/api/v1/files/pname?embed=mdr')
    assert file.status_code == 400


def test_delete_file_by_id(admin, jobstate_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'name'}
    file = admin.post('/api/v1/files', headers=headers)
    file_id = file.data['file']['id']

    url = '/api/v1/files/%s' % file_id

    created_file = admin.get(url)
    assert created_file.status_code == 200

    deleted_file = admin.delete(url)
    assert deleted_file.status_code == 204

    gfile = admin.get(url)
    assert gfile.status_code == 404

# Tests for the isolation


def test_create_file_as_user(user, jobstate_user_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
               'DCI-NAME': 'name'}
    file = user.post('/api/v1/files',
                     headers=headers)
    assert file.status_code == 201


@pytest.mark.usefixtures('file_id', 'file_user_id')
def test_get_all_files_as_user(user, team_user_id):
    files = user.get('/api/v1/files')
    assert files.status_code == 200
    assert files.data['_meta']['count']
    for file in files.data['files']:
        assert file['team_id'] == team_user_id


def test_get_file_as_user(user, file_id, jobstate_user_id):
    file = user.get('/api/v1/files/%s' % file_id)
    assert file.status_code == 404

    headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
               'DCI-NAME': 'name'}
    file = user.post('/api/v1/files', headers=headers).data
    file_id = file['file']['id']
    file = user.get('/api/v1/files/%s' % file_id)
    assert file.status_code == 200


def test_delete_file_as_user(user, admin, jobstate_user_id,
                             file_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
               'DCI-NAME': 'name2'}
    file_user = user.post('/api/v1/files',
                          headers=headers)
    file_user_id = file_user.data['file']['id']
    file_user = user.get('/api/v1/files/%s' % file_user_id)

    file_delete = user.delete('/api/v1/files/%s' % file_user_id)
    assert file_delete.status_code == 204

    file_user = admin.get('/api/v1/files/%s' % file_id)
    file_delete = user.delete('/api/v1/files/%s' % file_id)
    assert file_delete.status_code == 401


# This is no more valid
def loltest_get_file_content(admin, file_id):
    url = '/api/v1/files/%s/content' % file_id
    f = admin.get(url).data

    assert f['content'] == 'kikoolol'

    # retrieve the html form
    f = admin.get(url, headers={'Accept': 'text/html'})
    headers = f.headers
    data = f.data

    assert headers['Content-Disposition'] == 'attachment; filename=name'
    assert data.decode('utf8') == 'kikoolol'


def test_get_file_content(admin, jobstate_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'test_name'}
    data = "azertyuiop1234567890"
    file = admin.post('/api/v1/files', headers=headers, data=data).data
    file_id = file['file']['id']

    url = '/api/v1/files/%s/content' % file_id

    get_file = admin.get(url)

    assert get_file.status_code == 200
    # in the files controller, when it reads the file, Python will delimit
    # the data with quotes
    if type(get_file.data) == six.binary_type:
        assert get_file.data.decode('utf-8')[1:-1] == data
    else:
        assert get_file.data[1:-1] == data


def test_get_file_content_as_user(user, file_id, file_user_id):
    url = '/api/v1/files/%s/content'

    assert user.get(url % file_id).status_code == 401
    assert user.get(url % file_user_id).status_code == 200
