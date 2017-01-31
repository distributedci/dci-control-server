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

from __future__ import unicode_literals
import pytest


def test_create_remotecis(admin, team_id):
    pr = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id}).data
    pr_id = pr['remoteci']['id']
    gr = admin.get('/api/v1/remotecis/%s' % pr_id).data
    assert gr['remoteci']['name'] == 'pname'


def test_create_remotecis_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/remotecis',
                              data={'name': 'pname',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/remotecis',
                              data={'name': 'pname',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 422


def test_create_unique_remoteci_against_teams(admin, team_admin_id,
                                              team_user_id):
    data = {'name': 'foo', 'team_id': team_user_id}
    res = admin.post('/api/v1/remotecis', data=data)
    assert res.status_code == 201

    res = admin.post('/api/v1/remotecis', data=data)
    assert res.status_code == 422

    data['team_id'] = team_admin_id
    res = admin.post('/api/v1/remotecis', data=data)
    assert res.status_code == 201


def test_get_all_remotecis(admin, team_id):
    remoteci_1 = admin.post('/api/v1/remotecis',
                            data={'name': 'pname1', 'team_id': team_id}).data
    remoteci_2 = admin.post('/api/v1/remotecis',
                            data={'name': 'pname2', 'team_id': team_id}).data

    db_all_remotecis = admin.get('/api/v1/remotecis?sort=created_at').data
    db_all_remotecis = db_all_remotecis['remotecis']
    db_all_remotecis_ids = [db_t['id'] for db_t in db_all_remotecis]

    assert db_all_remotecis_ids == [remoteci_1['remoteci']['id'],
                                    remoteci_2['remoteci']['id']]


def test_get_all_remotecis_with_where(admin, team_id):
    pr = admin.post('/api/v1/remotecis', data={'name': 'pname1',
                                               'team_id': team_id}).data
    pr_id = pr['remoteci']['id']

    db_r = admin.get('/api/v1/remotecis?where=id:%s' % pr_id).data
    db_r_id = db_r['remotecis'][0]['id']
    assert db_r_id == pr_id

    db_r = admin.get('/api/v1/remotecis?where=name:pname1').data
    db_r_id = db_r['remotecis'][0]['id']
    assert db_r_id == pr_id


def test_get_all_remotecis_with_last_job(admin, team_id, remoteci_id,
                                         components_ids, topic_id):

    data = {'name': 'idle', 'team_id': team_id}
    idle_remoteci = admin.post('/api/v1/remotecis', data=data).data
    admin.post('/api/v1/topics/%s/teams' % topic_id,
               data={'team_id': team_id})
    data = {'name': 'foo', 'topic_id': topic_id,
            'component_types': ['type_1', 'type_2', 'type_3']}
    admin.post('/api/v1/jobdefinitions', data=data).data
    remotecis = admin.get((
        '/api/v1/remotecis?embed='
        'team,'
        'last_job,'
        'last_job.components,'
        'current_job,'
        'current_job.components')).data
    assert len(remotecis['remotecis']) == 2
    assert 'id' not in remotecis['remotecis'][0]['current_job']
    assert 'id' not in remotecis['remotecis'][0]['last_job']
    assert 'id' not in remotecis['remotecis'][1]['current_job']
    assert 'id' not in remotecis['remotecis'][1]['last_job']

    admin.post('/api/v1/jobs/schedule',
               data={'remoteci_id': remoteci_id,
                     'topic_id': topic_id})
    remotecis = admin.get((
        '/api/v1/remotecis?embed='
        'team,'
        'last_job,'
        'last_job.components,'
        'current_job,'
        'current_job.components')).data
    assert len(remotecis['remotecis']) == 2
    assert 'id' in remotecis['remotecis'][0]['current_job']
    assert len(remotecis['remotecis'][0]['current_job']['components']) == 3
    assert 'id' not in remotecis['remotecis'][0]['last_job']
    assert 'id' not in remotecis['remotecis'][1]['current_job']
    assert 'id' not in remotecis['remotecis'][1]['last_job']

    admin.post('/api/v1/jobs/schedule',
               data={'remoteci_id': remoteci_id,
                     'topic_id': topic_id})
    remotecis = admin.get((
        '/api/v1/remotecis?embed='
        'team,'
        'last_job,'
        'last_job.components,'
        'current_job,'
        'current_job.components')).data
    assert 'id' in remotecis['remotecis'][0]['current_job']
    assert 'id' in remotecis['remotecis'][0]['last_job']
    assert 'id' not in remotecis['remotecis'][1]['current_job']
    assert 'id' not in remotecis['remotecis'][1]['last_job']

    admin.post('/api/v1/jobs/schedule',
               data={'remoteci_id': idle_remoteci['remoteci']['id'],
                     'topic_id': topic_id})
    remotecis = admin.get((
        '/api/v1/remotecis?embed='
        'team,'
        'last_job,'
        'last_job.components,'
        'current_job,'
        'current_job.components')).data
    assert 'id' in remotecis['remotecis'][0]['current_job']
    assert 'id' in remotecis['remotecis'][0]['last_job']
    assert 'id' in remotecis['remotecis'][1]['current_job']
    assert 'id' not in remotecis['remotecis'][1]['last_job']

    admin.post('/api/v1/jobs/schedule',
               data={'remoteci_id': idle_remoteci['remoteci']['id'],
                     'topic_id': topic_id})
    remotecis = admin.get((
        '/api/v1/remotecis?embed='
        'team,'
        'last_job,'
        'last_job.components,'
        'current_job,'
        'current_job.components')).data
    assert 'id' in remotecis['remotecis'][0]['current_job']
    assert 'id' in remotecis['remotecis'][0]['last_job']
    assert 'id' in remotecis['remotecis'][1]['current_job']
    assert 'id' in remotecis['remotecis'][1]['last_job']

    assert len(remotecis['remotecis'][0]['last_job']['components']) == 3
    assert len(remotecis['remotecis'][1]['current_job']['components']) == 3
    assert len(remotecis['remotecis'][1]['last_job']['components']) == 3


def test_where_invalid(admin):
    err = admin.get('/api/v1/remotecis?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_remotecis_with_pagination(admin, team_id):
    # create 4 components types and check meta data count
    admin.post('/api/v1/remotecis', data={'name': 'pname1',
                                          'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname2',
                                          'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname3',
                                          'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname4',
                                          'team_id': team_id})
    remotecis = admin.get('/api/v1/remotecis').data
    assert remotecis['_meta']['count'] == 4

    # verify limit and offset are working well
    remotecis = admin.get('/api/v1/remotecis?limit=2&offset=0').data
    assert len(remotecis['remotecis']) == 2

    remotecis = admin.get('/api/v1/remotecis?limit=2&offset=2').data
    assert len(remotecis['remotecis']) == 2

    # if offset is out of bound, the api returns an empty list
    remotecis = admin.get('/api/v1/remotecis?limit=5&offset=300')
    assert remotecis.status_code == 200
    assert remotecis.data['remotecis'] == []


def test_get_all_remotecis_with_sort(admin, team_id):
    # create 2 remotecis ordered by created time
    r_1 = admin.post('/api/v1/remotecis',
                     data={'name': 'pname1',
                           'team_id': team_id}).data['remoteci']
    r_2 = admin.post('/api/v1/remotecis',
                     data={'name': 'pname2',
                           'team_id': team_id}).data['remoteci']

    grs = admin.get('/api/v1/remotecis?sort=created_at').data
    assert grs['remotecis'] == [r_1, r_2]

    # test in reverse order
    grs = admin.get('/api/v1/remotecis?sort=-created_at').data
    assert grs['remotecis'] == [r_2, r_1]


def test_get_all_remotecis_embed(admin, team_id):
    team = admin.get('/api/v1/teams/%s' % team_id).data['team']
    # create 2 remotecis
    admin.post('/api/v1/remotecis',
               data={'name': 'pname1', 'team_id': team_id})
    admin.post('/api/v1/remotecis',
               data={'name': 'pname2', 'team_id': team_id})

    # verify embed
    remotecis = admin.get('/api/v1/remotecis?embed=team').data

    for remoteci in remotecis['remotecis']:
        assert 'team_id' not in remoteci
        assert remoteci['team'] == team


def test_get_remoteci_by_id_or_name(admin, team_id):
    pr = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id}).data
    pr_id = pr['remoteci']['id']

    # get by uuid
    created_r = admin.get('/api/v1/remotecis/%s' % pr_id)
    assert created_r.status_code == 200

    created_r = created_r.data
    assert created_r['remoteci']['id'] == pr_id

    # get by name
    created_r = admin.get('/api/v1/remotecis/pname')
    assert created_r.status_code == 200

    created_r = created_r.data
    assert created_r['remoteci']['id'] == pr_id


def test_get_remoteci_with_embed(admin, team_id):
    team = admin.get('/api/v1/teams/%s' % team_id).data['team']
    premoteci = admin.post('/api/v1/remotecis',
                           data={'name': 'pname1', 'team_id': team_id}).data
    r_id = premoteci['remoteci']['id']

    # verify embed
    db_remoteci = admin.get('/api/v1/remotecis/%s?embed=team' % r_id).data
    assert 'team_id' not in premoteci
    assert db_remoteci['remoteci']['team'] == team


def test_get_remoteci_not_found(admin):
    result = admin.get('/api/v1/remotecis/ptdr')
    assert result.status_code == 404


def test_get_remoteci_data(admin, team_id):
    data_data = {'key': 'value'}
    data = {
        'name': 'pname1',
        'team_id': team_id,
        'data': data_data
    }

    premoteci = admin.post('/api/v1/remotecis', data=data).data

    r_id = premoteci['remoteci']['id']

    r_data = admin.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == data_data


def test_get_remoteci_data_specific_keys(admin, team_id):
    data_key = {'key': 'value'}
    data_key1 = {'key1': 'value1'}

    final_data = {}
    final_data.update(data_key)
    final_data.update(data_key1)
    data = {
        'name': 'pname1',
        'team_id': team_id,
        'data': final_data
    }

    premoteci = admin.post('/api/v1/remotecis', data=data).data

    r_id = premoteci['remoteci']['id']

    r_data = admin.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == final_data

    r_data = admin.get('/api/v1/remotecis/%s/data?keys=key' % r_id).data
    assert r_data == data_key

    r_data = admin.get('/api/v1/remotecis/%s/data?keys=key1' % r_id).data
    assert r_data == data_key1

    r_data = admin.get('/api/v1/remotecis/%s/data?keys=key,key1' % r_id).data
    assert r_data == final_data


def test_put_remotecis(admin, team_id):
    pr = admin.post('/api/v1/remotecis', data={'name': 'pname',
                                               'team_id': team_id})
    assert pr.status_code == 201

    pr_etag = pr.headers.get("ETag")

    gr = admin.get('/api/v1/remotecis/pname')
    assert gr.status_code == 200

    ppr = admin.put('/api/v1/remotecis/pname',
                    data={'name': 'nname'},
                    headers={'If-match': pr_etag})
    assert ppr.status_code == 204

    gr = admin.get('/api/v1/remotecis/pname')
    assert gr.status_code == 404

    gr = admin.get('/api/v1/remotecis/nname')
    assert gr.status_code == 200


def test_put_remoteci_data(admin, team_id):
    data_data = {'key': 'value'}
    data = {
        'name': 'pname1',
        'team_id': team_id,
        'data': data_data
    }

    pr = admin.post('/api/v1/remotecis', data=data)

    pr_etag = pr.headers.get("ETag")

    # Check that data is what it is supposed to be
    r_id = pr.data['remoteci']['id']

    r_data = admin.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == data_data

    # Update the data that belong to this remoteci
    new_data = {'key': 'new_value', 'new_key': 'another_value'}
    ppr = admin.put('/api/v1/remotecis/%s' % r_id,
                    data={'data': new_data},
                    headers={'If-match': pr_etag})
    assert ppr.status_code == 204

    r_data = admin.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == new_data


def test_delete_remoteci_by_id(admin, team_id):
    pr = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id})
    pr_etag = pr.headers.get("ETag")
    pr_id = pr.data['remoteci']['id']
    assert pr.status_code == 201

    created_r = admin.get('/api/v1/remotecis/%s' % pr_id)
    assert created_r.status_code == 200

    deleted_r = admin.delete('/api/v1/remotecis/%s' % pr_id,
                             headers={'If-match': pr_etag})
    assert deleted_r.status_code == 204

    gr = admin.get('/api/v1/remotecis/%s' % pr_id)
    assert gr.status_code == 404


def test_delete_remoteci_not_found(admin):
    result = admin.delete('/api/v1/remotecis/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


def test_delete_remoteci_data(admin, team_id):
    data_data = {'key': 'value'}
    data = {
        'name': 'pname1',
        'team_id': team_id,
        'data': data_data
    }

    pr = admin.post('/api/v1/remotecis', data=data)

    pr_etag = pr.headers.get("ETag")

    # Check that data is what it is supposed to be
    r_id = pr.data['remoteci']['id']

    r_data = admin.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == data_data

    # Remove the data that belongs to this remoteci
    new_data = {'key': ''}
    ppr = admin.put('/api/v1/remotecis/%s' % r_id,
                    data={'data': new_data},
                    headers={'If-match': pr_etag})
    assert ppr.status_code == 204

    r_data = admin.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == {}


# Tests for the isolation

def test_create_remoteci_as_user(user, team_user_id, team_id):
    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_id})
    assert remoteci.status_code == 401

    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_user_id})
    assert remoteci.status_code == 201


@pytest.mark.usefixtures('remoteci_id', 'remoteci_user_id')
def test_get_all_remotecis_as_user(user, team_user_id):
    remotecis = user.get('/api/v1/remotecis')
    assert remotecis.status_code == 200
    assert remotecis.data['_meta']['count'] == 1
    for remoteci in remotecis.data['remotecis']:
        assert remoteci['team_id'] == team_user_id


def test_get_remoteci_as_user(user, team_user_id, remoteci_id):
    remoteci = user.get('/api/v1/remotecis/%s' % remoteci_id)
    assert remoteci.status_code == 404

    user.post('/api/v1/remotecis',
              data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/rname')
    assert remoteci.status_code == 200


def test_put_remoteci_as_user(user, team_user_id, remoteci_id, admin):
    user.post('/api/v1/remotecis',
              data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/rname')
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_put = user.put('/api/v1/remotecis/rname',
                            data={'name': 'nname',
                                  'allow_upgrade_job': True},
                            headers={'If-match': remoteci_etag})
    assert remoteci_put.status_code == 204

    remoteci = user.get('/api/v1/remotecis/nname').data['remoteci']
    assert remoteci['name'] == 'nname'
    assert remoteci['allow_upgrade_job'] is True

    remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_put = user.put('/api/v1/remotecis/%s' % remoteci_id,
                            data={'name': 'nname'},
                            headers={'If-match': remoteci_etag})
    assert remoteci_put.status_code == 401


def test_delete_remoteci_as_user(user, team_user_id, admin, remoteci_id):
    user.post('/api/v1/remotecis',
              data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/rname')
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_delete = user.delete('/api/v1/remotecis/rname',
                                  headers={'If-match': remoteci_etag})
    assert remoteci_delete.status_code == 204

    remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_delete = user.delete('/api/v1/remotecis/%s' % remoteci_id,
                                  headers={'If-match': remoteci_etag})
    assert remoteci_delete.status_code == 401


# Tests for remoteci and tests management
def test_add_test_to_remoteci_and_get(admin, test_id, team_user_id):
    # create a remoteci
    data = {'name': 'rname', 'team_id': team_user_id}
    pr = admin.post('/api/v1/remotecis', data=data).data
    pr_id = pr['remoteci']['id']

    # attach a test to remoteci
    url = '/api/v1/remotecis/%s/tests' % pr_id
    add_data = admin.post(url, data={'test_id': test_id}).data
    assert add_data['remoteci_id'] == pr_id
    assert add_data['test_id'] == test_id

    # get test from remoteci
    test_from_remoteci = admin.get(url).data
    assert test_from_remoteci['_meta']['count'] == 1
    assert test_from_remoteci['tests'][0]['id'] == test_id


def test_delete_test_from_remoteci(admin, test_id, team_user_id):
    # create a jobdefinition
    data = {'name': 'pname', 'team_id': team_user_id}
    pr = admin.post('/api/v1/remotecis', data=data).data
    pr_id = pr['remoteci']['id']

    # check that the jobdefinition a as test attached
    url = '/api/v1/remotecis/%s/tests' % pr_id
    admin.post(url, data={'test_id': test_id})
    test_from_remoteci = admin.get(
        '/api/v1/remotecis/%s/tests' % pr_id).data
    assert test_from_remoteci['_meta']['count'] == 1

    # unattach test from jobdefinition
    admin.delete('/api/v1/remotecis/%s/tests/%s' % (pr_id, test_id))
    test_from_remoteci = admin.get(url).data
    assert test_from_remoteci['_meta']['count'] == 0

    # verify test still exist on /tests
    c = admin.get('/api/v1/tests/%s' % test_id)
    assert c.status_code == 200


def test_change_remoteci_state(admin, remoteci_id):
    t = admin.get('/api/v1/remotecis/' + remoteci_id).data['remoteci']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/remotecis/' + remoteci_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 204
    rci = admin.get('/api/v1/remotecis/' + remoteci_id).data['remoteci']
    assert rci['state'] == 'inactive'


def test_change_remoteci_to_invalid_state(admin, remoteci_id):
    t = admin.get('/api/v1/remotecis/' + remoteci_id).data['remoteci']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/remotecis/' + remoteci_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_remoteci = admin.get('/api/v1/remotecis/' + remoteci_id)
    assert current_remoteci.status_code == 200
    assert current_remoteci.data['remoteci']['state'] == 'active'
