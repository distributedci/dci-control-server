# -*- coding: utf-8 -*-
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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import teams
from dci.api.v1 import users
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.db import models
from dci import auth_mechanism


@api.route('/teams/<uuid:team_id>/users/<uuid:user_id>', methods=['POST'])
@decorators.login_required
def add_user_to_team(user, team_id, user_id):
    # filter payload and role
    values = flask.request.json
    # todo: check role in models.ROLES
    role = values.get('role', 'USER')

    if user.is_not_product_owner(team_id):
        raise dci_exc.Unauthorized()

    if role == 'SUPER_ADMIN' or role == 'READ_ONLY_USER':
        if user.is_not_super_admin():
            raise dci_exc.Unauthorized()

    query = models.JOIN_USERS_TEAMS_ROLES.insert().values(
        user_id=user_id,
        team_id=team_id,
        role=role)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError as e:
        raise dci_exc.DCIException('Adding user to team failed: %s' % str(e))

    return flask.Response(None, 201, content_type='application/json')


def serialize_users(users):
    # get rid of the teams_roles prefix
    res = []
    for user in users:
        new_user = {}
        for k, v in user.items():
            if k.startswith('teams_roles_'):
                _, suffix = k.split('teams_roles_')
                if suffix == 'role':
                    new_user[suffix] = user[k]
            else:
                new_user[k] = v
        res.append(new_user)
    return res


@api.route('/teams/<uuid:team_id>/users', methods=['GET'])
@decorators.login_required
def get_users_from_team(user, team_id):
    args = schemas.args(flask.request.args.to_dict())
    _JUTR = models.JOIN_USERS_TEAMS_ROLES
    query = v1_utils.QueryBuilder(models.USERS, args,
                                  users._USERS_COLUMNS,
                                  ['password', 'team_id'],
                                  root_join_table=_JUTR,
                                  root_join_condition=sql.and_(_JUTR.c.user_id == models.USERS.c.id,  # noqa
                                                               _JUTR.c.team_id == team_id))  # noqa

    if user.is_not_product_owner(team_id) and user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()

    query.add_extra_condition(models.USERS.c.state != 'archived')

    rows = query.execute(fetchall=True)
    team_users = v1_utils.format_result(rows, models.USERS.name, args['embed'],
                                        users._EMBED_MANY)
    team_users = serialize_users(team_users)

    return flask.jsonify({'users': team_users, '_meta': {'count': len(rows)}})


def serialize_teams(teams):
    # get rid of the teams_roles prefix
    res = []
    for team in teams:
        new_team = {}
        for k, v in team.items():
            if k == 'users':
                new_team['role'] = team['users']['teams_roles_role']
            else:
                new_team[k] = v
        res.append(new_team)
    return res


def get_child_teams_ids(user_teams):
    all_teams = auth_mechanism.BaseMechanism.get_all_teams()
    child_teams_ids = []
    for u_t in user_teams:
        for a_team in all_teams:
            if a_team['parent_id'] == u_t['id']:
                child_teams_ids.append(a_team['id'])
    return child_teams_ids


@api.route('/users/<uuid:user_id>/teams', methods=['GET'])
@decorators.login_required
def get_teams_of_user(user, user_id):
    v1_utils.verify_existence_and_get(user_id, models.USERS)
    if user.is_super_admin():
        # get the all the full teams associated to the user_id
        user_teams = teams._get_user_teams(user_id)
    else:
        # get all the teams associated to the user_id but only the teams
        # that belongs to the child teams of the caller
        # ie. a product owner should only see the teams of the user that it's
        # under it's product team
        user_teams = teams._get_user_teams(user_id, user.child_teams_ids)
    # for each team get their child teams
    # this is usefull for the super admin to see the child teams
    # of a product team
    child_teams_ids = get_child_teams_ids(user_teams)
    child_teams = teams._get_user_child_teams(child_teams_ids)

    return flask.jsonify({'teams': user_teams,
                          'child_teams': child_teams,
                          '_meta': {'count': len(user_teams) + len(child_teams)}})  # noqa


@api.route('/teams/<uuid:team_id>/users/<uuid:user_id>', methods=['DELETE'])
@decorators.login_required
def remove_user_from_team(user, team_id, user_id):

    if user.is_not_product_owner(team_id):
        raise dci_exc.Unauthorized()

    _JUTR = models.JOIN_USERS_TEAMS_ROLES
    query = _JUTR.delete().where(sql.and_(_JUTR.c.user_id == user_id,
                                          _JUTR.c.team_id == team_id))
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')
