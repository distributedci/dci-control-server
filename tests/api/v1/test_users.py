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
import uuid


def test_create_users(admin, team_id, role_user):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname', 'password': 'ppass',
                          'team_id': team_id}).data

    pu_id = pu['user']['id']
    assert pu['user']['role_id'] == role_user['id']
    gu = admin.get('/api/v1/users/%s' % pu_id).data
    assert gu['user']['name'] == 'pname'


def test_create_unique_user_against_teams(admin, team_admin_id, team_user_id):
    data = {'name': 'foo', 'password': 'psswd', 'team_id': team_user_id}
    res = admin.post('/api/v1/users', data=data)
    assert res.status_code == 201

    res = admin.post('/api/v1/users', data=data)
    assert res.status_code == 409

    data['team_id'] = team_admin_id
    res = admin.post('/api/v1/users', data=data)
    assert res.status_code == 409


def test_create_users_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 409


def test_get_all_users(admin, team_id):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?sort=created_at').data
    db_users = db_users['users']
    db_users_ids = [db_t['id'] for db_t in db_users]

    user_1 = admin.post('/api/v1/users', data={'name': 'pname1',
                                               'password': 'ppass',
                                               'team_id': team_id}).data
    user_2 = admin.post('/api/v1/users', data={'name': 'pname2',
                                               'password': 'ppass',
                                               'team_id': team_id}).data
    db_users_ids.extend([user_1['user']['id'], user_2['user']['id']])

    db_all_users = admin.get('/api/v1/users?sort=created_at').data
    db_all_users = db_all_users['users']
    db_all_users_ids = [db_t['id'] for db_t in db_all_users]

    assert db_all_users_ids == db_users_ids


def test_get_all_users_with_team(admin):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?embed=team&where=name:admin').data
    db_users = db_users['users']
    assert db_users[0]['team']['id']


def test_get_all_users_with_role(admin):
    db_users = admin.get(
        '/api/v1/users?embed=role&where=name:admin'
    ).data['users']

    assert db_users[0]['role']['label'] == 'SUPER_ADMIN'


def test_get_all_users_with_where(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname1',
                                           'password': 'ppass',
                                           'team_id': team_id}).data
    pu_id = pu['user']['id']

    db_u = admin.get('/api/v1/users?where=id:%s' % pu_id).data
    db_u_id = db_u['users'][0]['id']
    assert db_u_id == pu_id

    db_u = admin.get('/api/v1/users?where=name:pname1').data
    db_u_id = db_u['users'][0]['id']
    assert db_u_id == pu_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/users?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_users_with_pagination(admin, team_id):
    # create 4 components types and check meta data count
    admin.post('/api/v1/users', data={'name': 'pname1',
                                      'password': 'ppass',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname2',
                                      'password': 'ppass',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname3',
                                      'password': 'ppass',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname4',
                                      'password': 'ppass',
                                      'team_id': team_id})
    users = admin.get('/api/v1/users').data
    assert users['_meta']['count'] == 7

    # verify limit and offset are working well
    users = admin.get('/api/v1/users?limit=2&offset=0').data
    assert len(users['users']) == 2

    users = admin.get('/api/v1/users?limit=2&offset=2').data
    assert len(users['users']) == 2

    # if offset is out of bound, the api returns an empty list
    users = admin.get('/api/v1/users?limit=5&offset=300')
    assert users.status_code == 200
    assert users.data['users'] == []


def test_get_all_users_with_sort(admin, team_id):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?sort=created_at').data
    db_users = db_users['users']

    # create 2 users ordered by created time
    user_1 = admin.post('/api/v1/users',
                        data={'name': 'pname1',
                              'password': 'ppass',
                              'team_id': team_id}).data['user']

    user_2 = admin.post('/api/v1/users',
                        data={'name': 'pname2',
                              'password': 'ppass',
                              'team_id': team_id}).data['user']

    gusers = admin.get('/api/v1/users?sort=created_at').data
    db_users.extend([user_1, user_2])
    assert gusers['users'] == db_users

    # test in reverse order
    db_users.reverse()
    gusers = admin.get('/api/v1/users?sort=-created_at').data
    assert gusers['users'] == db_users


def test_get_user_by_id(admin, team_id):
    puser = admin.post('/api/v1/users',
                       data={'name': 'pname',
                             'password': 'ppass',
                             'team_id': team_id}).data
    puser_id = puser['user']['id']

    # get by uuid
    created_user = admin.get('/api/v1/users/%s' % puser_id)
    assert created_user.status_code == 200

    created_user = created_user.data
    assert created_user['user']['id'] == puser_id


def test_get_user_not_found(admin):
    result = admin.get('/api/v1/users/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_put_users(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'team_id': team_id})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 204

    gu = admin.get('/api/v1/users/%s' % gu.data['user']['id'])
    assert gu.data['user']['name'] == 'nname'


def test_change_user_state(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'team_id': team_id})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'state': 'inactive'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 204

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200
    assert gu.data['user']['state'] == 'inactive'


def test_change_user_to_invalid_state(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'team_id': team_id})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'state': 'kikoolol'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 400

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200
    assert gu.data['user']['state'] == 'active'


def test_delete_user_by_id(admin, team_id):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname',
                          'password': 'ppass',
                          'team_id': team_id})
    pu_etag = pu.headers.get("ETag")
    pu_id = pu.data['user']['id']
    assert pu.status_code == 201

    created_user = admin.get('/api/v1/users/%s' % pu_id)
    assert created_user.status_code == 200

    deleted_user = admin.delete('/api/v1/users/%s' % pu_id,
                                headers={'If-match': pu_etag})
    assert deleted_user.status_code == 204

    gu = admin.get('/api/v1/users/%s' % pu_id)
    assert gu.status_code == 404


def test_delete_user_not_found(admin):
    result = admin.delete('/api/v1/users/%s' % uuid.uuid4(),
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for the isolation

def test_create_user_as_user(user, user_admin, team_user_id):
    # simple user cannot add a new user to its team
    pu = user.post('/api/v1/users',
                   data={'name': 'pname',
                         'password': 'ppass',
                         'team_id': team_user_id})
    assert pu.status_code == 401

    # admin user can add a new user to its team
    pu = user_admin.post('/api/v1/users',
                         data={'name': 'pname',
                               'password': 'ppass',
                               'team_id': team_user_id})
    assert pu.status_code == 201


def test_get_all_users_as_user(user, team_user_id):
    # 2 users already exists for tests: user_admin, user, so we can directly
    # retrieve informations without inserting new entries
    users = user.get('/api/v1/users')
    assert users.status_code == 200
    assert users.data['_meta']['count'] == 2
    for guser in users.data['users']:
        assert guser['team_id'] == team_user_id


def test_get_user_as_user(user, admin):
    # admin does not belong to this user's team
    padmin = admin.get('/api/v1/users?where=name:admin')
    padmin = admin.get('/api/v1/users/%s' % padmin.data['users'][0]['id'])

    puser = user.get('/api/v1/users?where=name:user')
    puser = user.get('/api/v1/users/%s' % puser.data['users'][0]['id'])

    guser = user.get('/api/v1/users/%s' % padmin.data['user']['id'])
    assert guser.status_code == 404

    guser = user.get('/api/v1/users/%s' % puser.data['user']['id'])
    assert guser.status_code == 200


# Only super admin and an admin of a team can update the user
def test_put_user_as_user_admin(user, user_admin):

    puser = user.get('/api/v1/users?where=name:user')
    puser = user.get('/api/v1/users/%s' % puser.data['users'][0]['id'])
    user_etag = puser.headers.get("ETag")

    user_put = user.put('/api/v1/users/%s' % puser.data['user']['id'],
                        data={'name': 'nname'},
                        headers={'If-match': user_etag})
    assert user_put.status_code == 401

    user_put = user_admin.put('/api/v1/users/%s' % puser.data['user']['id'],
                              data={'name': 'nname'},
                              headers={'If-match': user_etag})
    assert user_put.status_code == 204


# Only super admin can delete a team
def test_delete_as_user_admin(user, user_admin):
    puser = user.get('/api/v1/users?where=name:user')
    puser = user.get('/api/v1/users/%s' % puser.data['users'][0]['id'])
    user_etag = puser.headers.get("ETag")

    user_delete = user.delete('/api/v1/users/%s' % puser.data['user']['id'],
                              headers={'If-match': user_etag})
    assert user_delete.status_code == 401

    user_delete = user_admin.delete('/api/v1/users/%s'
                                    % puser.data['user']['id'],
                                    headers={'If-match': user_etag})
    assert user_delete.status_code == 204


def test_success_update_field_by_field(admin, team_id):
    user = admin.post('/api/v1/users',
                      data={'name': 'pname', 'password': 'ppass',
                            'team_id': team_id}).data['user']

    t = admin.get('/api/v1/users/%s' % user['id']).data['user']

    admin.put('/api/v1/users/%s' % user['id'],
              data={'state': 'inactive'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/users/%s' % user['id']).data['user']

    assert t['name'] == 'pname'
    assert t['state'] == 'inactive'

    admin.put('/api/v1/users/%s' % user['id'],
              data={'name': 'newuser'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/users/%s' % user['id']).data['user']

    assert t['name'] == 'newuser'
    assert t['state'] == 'inactive'


def test_get_current_user(user):
    request = user.get('/api/v1/users/me')
    assert request.status_code == 200

    me = request.data['user']
    expected_user = user.get('/api/v1/users?where=name:user').data['users'][0]

    assert me['id'] == expected_user['id']
    for key in expected_user.keys():
        assert me[key] == expected_user[key]
