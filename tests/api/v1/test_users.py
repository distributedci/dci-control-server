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
                          'fullname': 'P Name', 'email': 'pname@example.org',
                          'team_id': team_id}).data

    pu_id = pu['user']['id']
    assert pu['user']['role_id'] == role_user['id']
    gu = admin.get('/api/v1/users/%s' % pu_id).data
    assert gu['user']['name'] == 'pname'
    assert gu['user']['timezone'] == 'UTC'


def test_create_unique_user_against_teams(admin, team_admin_id, team_user_id):
    data = {'name': 'foo', 'password': 'psswd', 'team_id': team_user_id,
            'fullname': 'Foo Bar', 'email': 'foo@example.org'}

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
                                    'fullname': 'P Name',
                                    'email': 'pname@example.org',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'fullname': 'P Name',
                                    'email': 'pname@example.org',
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
                                               'fullname': 'P Name',
                                               'email': 'pname@example.org',
                                               'team_id': team_id}).data
    user_2 = admin.post('/api/v1/users', data={'name': 'pname2',
                                               'password': 'ppass',
                                               'fullname': 'Q Name',
                                               'email': 'qname@example.org',
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
                                           'fullname': 'P Name',
                                           'email': 'pname@example.org',
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
    users = admin.get('/api/v1/users').data
    current_users = users['_meta']['count']
    # create 4 components types and check meta data count
    admin.post('/api/v1/users', data={'name': 'pname1',
                                      'password': 'ppass',
                                      'fullname': 'P Name',
                                      'email': 'pname@example.org',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname2',
                                      'password': 'ppass',
                                      'fullname': 'Q Name',
                                      'email': 'qname@example.org',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname3',
                                      'password': 'ppass',
                                      'fullname': 'R Name',
                                      'email': 'rname@example.org',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname4',
                                      'password': 'ppass',
                                      'fullname': 'S Name',
                                      'email': 'sname@example.org',
                                      'team_id': team_id})
    users = admin.get('/api/v1/users').data
    assert users['_meta']['count'] == current_users + 4

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
                              'fullname': 'P Name',
                              'email': 'pname@example.org',
                              'team_id': team_id}).data['user']

    user_2 = admin.post('/api/v1/users',
                        data={'name': 'pname2',
                              'password': 'ppass',
                              'fullname': 'Q Name',
                              'email': 'qname@example.org',
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
                             'fullname': 'P Name',
                             'email': 'pname@example.org',
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
                                           'fullname': 'P Name',
                                           'timezone': 'Europe/Paris',
                                           'email': 'pname@example.org',
                                           'team_id': team_id})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200
    assert gu.data['user']['timezone'] == 'Europe/Paris'

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 200
    assert ppu.data['user']['name'] == 'nname'


def test_change_user_state(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'email': 'pname@example.org',
                                           'team_id': team_id})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'state': 'inactive'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 200
    assert ppu.data['user']['state'] == 'inactive'


def test_change_user_to_invalid_state(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'email': 'pname@example.org',
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
                          'fullname': 'P Name',
                          'email': 'pname@example.org',
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


def test_delete_user_with_no_team(admin, user_no_team):
    deleted_user = admin.delete('/api/v1/users/%s' % user_no_team['id'],
                                headers={'If-match': user_no_team['etag']})
    assert deleted_user.status_code == 204


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
                         'fullname': 'P Name',
                         'email': 'pname@example.org',
                         'team_id': team_user_id})
    assert pu.status_code == 401

    # admin user can add a new user to its team
    pu = user_admin.post('/api/v1/users',
                         data={'name': 'pname',
                               'password': 'ppass',
                               'fullname': 'P Name',
                               'email': 'pname@example.org',
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


def get_user(flask_user, name):
    get = flask_user.get('/api/v1/users?where=name:%s' % name)
    get2 = flask_user.get('/api/v1/users/%s' % get.data['users'][0]['id'])
    return get2.data['user'], get2.headers.get("ETag")


def test_admin_or_team_admin_can_update_another_user(admin, user_admin):
    user, etag = get_user(admin, 'user')
    assert admin.put(
        '/api/v1/users/%s' % user['id'],
        data={'name': 'new_name'},
        headers={'If-match': etag}
    ).status_code == 200

    user, etag = get_user(admin, 'new_name')
    assert user_admin.put(
        '/api/v1/users/%s' % user['id'],
        data={'name': 'user'},
        headers={'If-match': etag}
    ).status_code == 200


def test_user_cant_update_him(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.put(
        '/api/v1/users/%s' % user_data['id'],
        data={'name': 'new_name'},
        headers={'If-match': user_etag}
    ).status_code == 401


# Only super admin can delete a user
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
                            'fullname': 'P Name', 'email': 'pname@example.org',
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


def test_update_current_user_password(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    assert user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': 'password'},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/users/me').status_code == 401

    user_data, user_etag = get_user(admin, 'user')

    assert admin.put(
        '/api/v1/users/%s' % user_data['id'],
        data={'password': 'user'},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/users/me').status_code == 200


def test_update_current_user_current_password_wrong(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    assert user.put(
        '/api/v1/users/me',
        data={'current_password': 'wrong_password', 'new_password': ''},
        headers={'If-match': user_etag}
    ).status_code == 400

    assert user.get('/api/v1/users/me').status_code == 200


def test_update_current_user_new_password_empty(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    assert user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': ''},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/users/me').status_code == 200


def test_update_current_user(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    me = user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': '',
              'email': 'new_email@example.org', 'fullname': 'New Name',
              'timezone': 'Europe/Paris'},
        headers={'If-match': user_etag}
    )
    assert me.status_code == 200
    assert me.data['user']['email'] == 'new_email@example.org'
    assert me.data['user']['fullname'] == 'New Name'
    assert me.data['user']['timezone'] == 'Europe/Paris'


def test_get_embed_remotecis(user, remoteci_user_id, user_id):
    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)

    assert r.status_code == 201

    me = user.get('/api/v1/users/me?embed=remotecis').data['user']
    assert me['remotecis'][0]['id'] == remoteci_user_id


def test_user_cannot_update_team(user, user_id, team_admin_id):
    guser = user.get('/api/v1/users/%s' % user_id)
    etag = guser.data['user']['etag']
    data = {'team_id': team_admin_id}
    r = user.put('/api/v1/users/%s' % user_id, data=data,
                 headers={'If-match': etag})
    assert r.status_code == 401

    guser = user.get('/api/v1/users/%s' % user_id)
    assert guser.data['user']['team_id'] != team_admin_id


def test_team_admin_user_cannot_update_team(user_admin, user, user_id,
                                            team_admin_id):
    guser = user.get('/api/v1/users/%s' % user_id)
    etag = guser.data['user']['etag']
    data = {'team_id': team_admin_id}
    r = user_admin.put('/api/v1/users/%s' % user_id, data=data,
                       headers={'If-match': etag})
    assert r.status_code == 401


def test_success_ensure_put_me_api_secret_is_not_leaked(admin, user):
    """Test to ensure API secret is not leaked during update."""

    user_data, user_etag = get_user(admin, 'user')

    res = user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': 'password'},
        headers={'If-match': user_etag}
    )

    assert res.status_code == 200
    assert 'password' not in res.data['user']


def test_success_ensure_put_api_secret_is_not_leaked(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'timezone': 'Europe/Paris',
                                           'email': 'pname@example.org',
                                           'team_id': team_id})
    pu_etag = pu.headers.get("ETag")
    ppu = admin.put('/api/v1/users/%s' % pu.data['user']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 200
    assert 'password' not in ppu.data['user']
