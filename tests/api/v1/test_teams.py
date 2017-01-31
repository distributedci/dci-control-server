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


def test_create_teams(admin):
    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname'}).data
    pt_id = pt['team']['id']
    gt = admin.get('/api/v1/teams/%s' % pt_id).data
    assert gt['team']['name'] == 'pname'


def test_create_teams_already_exist(admin):
    pstatus_code = admin.post('/api/v1/teams',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/teams',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 422


def test_get_all_teams(admin):
    # TODO(yassine): Currently there is already 3 teams created in the DB,
    # this will be fixed later.
    db_teams = admin.get('/api/v1/teams?sort=created_at').data
    db_teams = db_teams['teams']
    db_teams_ids = [db_t['id'] for db_t in db_teams]

    test_1 = admin.post('/api/v1/teams', data={'name': 'pname1'}).data
    test_2 = admin.post('/api/v1/teams', data={'name': 'pname2'}).data
    db_teams_ids.extend([test_1['team']['id'], test_2['team']['id']])

    db_get_all_teams = admin.get('/api/v1/teams?sort=created_at').data
    db_get_all_teams = db_get_all_teams['teams']
    db_get_all_teams_ids = [db_t['id'] for db_t in db_get_all_teams]

    assert db_get_all_teams_ids == db_teams_ids


def test_get_all_teams_with_where(admin):
    pt = admin.post('/api/v1/teams', data={'name': 'pname1'}).data
    pt_id = pt['team']['id']

    db_t = admin.get('/api/v1/teams?where=id:%s' % pt_id).data
    db_t_id = db_t['teams'][0]['id']
    assert db_t_id == pt_id

    db_t = admin.get('/api/v1/teams?where=name:pname1').data
    db_t_id = db_t['teams'][0]['id']
    assert db_t_id == pt_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/teams?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_teams_with_pagination(admin):
    # create 4 components types and check meta data count
    admin.post('/api/v1/teams', data={'name': 'pname1'})
    admin.post('/api/v1/teams', data={'name': 'pname2'})
    admin.post('/api/v1/teams', data={'name': 'pname3'})
    admin.post('/api/v1/teams', data={'name': 'pname4'})
    ts = admin.get('/api/v1/teams').data
    # TODO(yassine): 2 teams was already created in the db
    assert ts['_meta']['count'] == 6

    # verify limit and offset are working well
    ts = admin.get('/api/v1/teams?limit=2&offset=0').data
    assert len(ts['teams']) == 2

    ts = admin.get('/api/v1/teams?limit=2&offset=2').data
    assert len(ts['teams']) == 2

    # if offset is out of bound, the api returns an empty list
    ts = admin.get('/api/v1/teams?limit=5&offset=300')
    assert ts.status_code == 200
    assert ts.data['teams'] == []


def test_get_all_teams_with_sort(admin):
    # TODO(yassine): Currently there is already 3 teams created in the DB,
    # this will be fixed later.
    db_teams = admin.get('/api/v1/teams?sort=created_at').data
    db_teams = db_teams['teams']

    # create 2 teams ordered by created time
    t_1 = admin.post('/api/v1/teams',
                     data={'name': 'pname1'}).data['team']
    t_2 = admin.post('/api/v1/teams',
                     data={'name': 'pname2'}).data['team']

    gts = admin.get('/api/v1/teams?sort=created_at').data
    db_teams.extend([t_1, t_2])
    assert gts['teams'] == db_teams

    # test in reverse order
    db_teams.reverse()
    gts = admin.get('/api/v1/teams?sort=-created_at').data
    assert gts['teams'] == db_teams


def test_get_team_by_id_or_name(admin):
    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname'}).data
    pt_id = pt['team']['id']

    # get by uuid
    created_t = admin.get('/api/v1/teams/%s' % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['team']['id'] == pt_id

    # get by name
    created_t = admin.get('/api/v1/teams/pname')
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['team']['id'] == pt_id


def test_get_team_not_found(admin):
    result = admin.get('/api/v1/teams/ptdr')
    assert result.status_code == 404


def test_put_teams(admin):
    pt = admin.post('/api/v1/teams', data={'name': 'pname'})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get('/api/v1/teams/pname')
    assert gt.status_code == 200

    ppt = admin.put('/api/v1/teams/pname',
                    data={'name': 'nname'},
                    headers={'If-match': pt_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/teams/pname')
    assert gt.status_code == 404

    gt = admin.get('/api/v1/teams/nname')
    assert gt.status_code == 200


def test_delete_team_by_id(admin):
    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname'})
    pt_etag = pt.headers.get("ETag")
    pt_id = pt.data['team']['id']
    assert pt.status_code == 201

    created_t = admin.get('/api/v1/teams/%s' % pt_id)
    assert created_t.status_code == 200

    deleted_t = admin.delete('/api/v1/teams/%s' % pt_id,
                             headers={'If-match': pt_etag})
    assert deleted_t.status_code == 204

    gt = admin.get('/api/v1/teams/%s' % pt_id)
    assert gt.status_code == 404


def test_delete_team_not_found(admin):
    result = admin.delete('/api/v1/teams/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for the isolation

def test_create_team_as_user(user):
    team = user.post('/api/v1/teams',
                     data={'name': 'pname'})
    assert team.status_code == 401


def test_get_all_teams_as_user(user):
    teams = user.get('/api/v1/teams')
    assert teams.status_code == 200


def test_get_teams_as_user(user):
    team = user.get('/api/v1/teams/admin')
    assert team.status_code == 401

    team = user.get('/api/v1/teams/user')
    assert team.status_code == 200

    teams = user.get('/api/v1/teams')
    assert teams.status_code == 200
    assert len(teams.data['teams']) == 1


# Only super admin and an admin of a team can update the team
def test_put_team_as_user_admin(user, user_admin):
    team = user.get('/api/v1/teams/user')
    team_etag = team.headers.get("ETag")
    team_user_id = team.data['team']['id']

    team_put = user.put('/api/v1/teams/%s' % team_user_id,
                        data={'name': 'nname'},
                        headers={'If-match': team_etag})
    assert team_put.status_code == 401

    team_put = user_admin.put('/api/v1/teams/%s' % team_user_id,
                              data={'name': 'nname'},
                              headers={'If-match': team_etag})
    assert team_put.status_code == 204


def test_change_team_state(admin, team_id):
    t = admin.get('/api/v1/teams/' + team_id).data['team']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/teams/' + team_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 204
    current_team = admin.get('/api/v1/teams/' + team_id).data['team']
    assert current_team['state'] == 'inactive'


def test_change_team_to_invalid_state(admin, team_id):
    t = admin.get('/api/v1/teams/' + team_id).data['team']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/teams/' + team_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_team = admin.get('/api/v1/teams/' + team_id)
    assert current_team.status_code == 200
    assert current_team.data['team']['state'] == 'active'


# Only super admin can delete a team
def test_delete_as_user_admin(user, user_admin):
    team = user.get('/api/v1/teams/user')
    team_etag = team.headers.get("ETag")

    team_delete = user.delete('/api/v1/teams/user',
                              headers={'If-match': team_etag})
    assert team_delete.status_code == 401

    team_delete = user_admin.delete('/api/v1/teams/user',
                                    headers={'If-match': team_etag})
    assert team_delete.status_code == 401


def test_get_tests_by_team(user, admin, team_user_id, team_admin_id):
    tests = user.get('/api/v1/teams/' + team_admin_id + '/tests/')
    assert tests.status_code == 401
    tests = user.get('/api/v1/teams/' + team_user_id + '/tests/')
    assert tests.status_code == 200
    assert tests.data['_meta']['count'] == 0


def test_list_tests_by_team(admin, team_id, test_id):
    tests = admin.get('/api/v1/teams/' + team_id + '/tests/')
    assert tests.status_code == 200
    assert tests.data['_meta']['count'] == 1
    assert tests.data['tests'][0]['team_id'] == team_id
    assert tests.data['tests'][0]['id'] == test_id
