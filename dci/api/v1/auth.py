# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Red Hat, Inc
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
import logging

import flask
from dci.common.schemas import check_json_is_valid, create_jwt_schema
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from sqlalchemy import orm, select

from dci.api.v1 import api
from dci.auth import check_passwords_equal
from dci.db import models2

logger = logging.getLogger(__name__)


def _get_user(email):
    if not email:
        return None
    try:
        query = (
            select(models2.User)
            .where(models2.User.email == email)
            .where(models2.User.state == "active")
        )
        return flask.g.session.execute(query).scalar_one_or_none()
    except orm.exc.NoResultFound:
        logger.debug(f"No user found with email {email}")
    return None


def _password_is_valid(password, user):
    if not password or not user.password:
        return False
    return check_passwords_equal(password, user.password)


@api.route("/auth/login", methods=["POST"])
def login():
    values = flask.request.json
    check_json_is_valid(create_jwt_schema, values)

    email = values["email"]
    password = values["password"]

    user = _get_user(email)
    if user is None or not _password_is_valid(password, user):
        return flask.jsonify({"msg": "Bad email or password"}), 401

    access_token = create_access_token(identity=user.email, fresh=True)
    refresh_token = create_refresh_token(identity=user.email)
    return flask.jsonify(access_token=access_token, refresh_token=refresh_token), 201


@api.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return flask.jsonify(access_token=access_token)
