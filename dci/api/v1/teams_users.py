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
import logging
from sqlalchemy import exc as sa_exc

from dci.api.v1 import api, base, utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.signature import gen_secret
from dci.db import models2
from dci.common.schemas import check_json_is_valid, team_users_create_schema


logger = logging.getLogger()


def _add_user_to_team(user_id, team_id):
    team = base.get_resource_orm(models2.Team, team_id)
    user = base.get_resource_orm(models2.User, user_id)

    try:
        team.users.append(user)
        flask.g.session.add(team)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="conflict when adding team", status_code=409)


@api.route("/teams/<uuid:team_id>/users/<uuid:user_id>", methods=["POST"])
@decorators.login_required
def add_user_to_team(user, team_id, user_id):
    if (
        team_id == flask.g.team_admin_id
        or team_id == flask.g.team_redhat_id
        or team_id == flask.g.team_epm_id
    ) and user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    if user.is_not_epm():
        raise dci_exc.Unauthorized()

    _add_user_to_team(user_id, team_id)

    return flask.Response(None, 201, content_type="application/json")


def _get_users_from_team(team_id):
    team = base.get_resource_orm(models2.Team, team_id)
    return [u.serialize() for u in team.users]


@api.route("/teams/<uuid:team_id>/users", methods=["GET"])
@decorators.login_required
def get_users_from_team(user, team_id):
    if user.is_not_epm() and user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()

    team_users = _get_users_from_team(team_id)

    return flask.jsonify({"users": team_users, "_meta": {"count": len(team_users)}})


@api.route("/teams/<uuid:team_id>/users", methods=["POST"])
@decorators.login_required
def get_or_create_users_to_team(user, team_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    emails = flask.request.json
    check_json_is_valid(team_users_create_schema, emails)

    for email in emails:
        try:
            values = utils.with_common_value(
                {
                    "name": email,
                    "fullname": email,
                    "sso_username": email,
                    "email": email,
                    "password": gen_secret(),
                }
            )
            filters = [models2.User.email == email]
            partner = base.get_or_create_resource_orm(models2.User, values, filters)
            _add_user_to_team(partner["id"], team_id)
        except sa_exc.DBAPIError as e:
            logger.error(
                "Error while creating user with email %s: %s" % (email, str(e))
            )
            flask.g.session.rollback()
            raise dci_exc.DCIException(str(e))

    team_users = _get_users_from_team(team_id)

    return flask.jsonify({"users": team_users, "_meta": {"count": len(team_users)}})


@api.route("/users/<uuid:user_id>/teams", methods=["GET"])
@decorators.login_required
def get_teams_of_user(user, user_id):
    if user.is_not_super_admin() and user.id != user_id and user.is_not_epm():
        raise dci_exc.Unauthorized()

    user = base.get_resource_orm(models2.User, user_id)
    user_teams = [t.serialize() for t in user.team]

    return flask.jsonify({"teams": user_teams, "_meta": {"count": len(user_teams)}})


@api.route("/teams/<uuid:team_id>/users/<uuid:user_id>", methods=["DELETE"])
@decorators.login_required
def remove_user_from_team(user, team_id, user_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = base.get_resource_orm(models2.Team, team_id)
    user = base.get_resource_orm(models2.User, user_id)

    try:
        team.users.remove(user)
        flask.g.session.add(team)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="conflict when user from team", status_code=409
        )

    return flask.Response(None, 204, content_type="application/json")
