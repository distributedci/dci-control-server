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


@api.route('/teams/<uuid:team_id>/users/<uuid:user_id>', methods=['POST'])
@decorators.login_required
@decorators.check_roles
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


def serialize(users):
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
@decorators.check_roles
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
    team_users = serialize(team_users)

    return flask.jsonify({'users': team_users, '_meta': {'count': len(rows)}})


@api.route('/users/<uuid:user_id>/teams', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_teams_of_user(user, user_id):
    args = schemas.args(flask.request.args.to_dict())
    _JUTR = models.JOIN_USERS_TEAMS_ROLES
    query = v1_utils.QueryBuilder(models.TEAMS, args,
                                  teams._T_COLUMNS,
                                  root_join_table=_JUTR,
                                  root_join_condition=sql.and_(_JUTR.c.team_id == models.TEAMS.c.id,  # noqa
                                                               _JUTR.c.user_id == user_id))  # noqa

    if user.is_not_super_admin() and user.id != user_id:
        raise dci_exc.Unauthorized()

    query.add_extra_condition(models.TEAMS.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, models.TEAMS.name, args['embed'],
                                  teams._EMBED_MANY)

    return flask.jsonify({'teams': rows, '_meta': {'count': nb_rows}})


@api.route('/teams/<uuid:team_id>/users/<uuid:user_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def remove_user_from_team(user, team_id, user_id):

    if user.is_not_product_owner(team_id):
        raise dci_exc.Unauthorized()

    _JUTR = models.JOIN_USERS_TEAMS_ROLES
    query = _JUTR.delete().where(sql.and_(_JUTR.c.user_id == user_id,
                                          _JUTR.c.team_id == team_id))
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')
