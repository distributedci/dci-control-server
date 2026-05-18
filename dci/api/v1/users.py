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
import flask
from flask import json
from sqlalchemy import exc as sa_exc, select, func, update
import sqlalchemy.orm as sa_orm

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import declarative as d
from dci.db import models2
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_user_schema,
    update_user_schema,
    update_current_user_schema,
    check_and_get_args,
)


@api.route("/users", methods=["POST"])
@decorators.login_required
def create_users(user):
    values = flask.request.json
    check_json_is_valid(create_user_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    sso_username = values.get("sso_username")
    email = values.get("email")
    default_name = email if email else sso_username
    password = (
        auth.hash_password(values.get("password")) if values.get("password") else None
    )
    values.update(
        {
            "name": values.get("name", default_name),
            "fullname": values.get("fullname", default_name),
            "password": password,
            "timezone": values.get("timezone", "UTC"),
        }
    )

    try:
        u = models2.User(**values)
        u_serialized = u.serialize(only_columns=models2.User.api_fields)
        flask.g.session.add(u)
        flask.g.session.commit()
    except sa_exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))

    return flask.Response(
        json.dumps({"user": u_serialized}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/users", methods=["GET"])
@decorators.login_required
def get_all_users(user):
    args = check_and_get_args(flask.request.args.to_dict())
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    query = (
        select(models2.User)
        .where(models2.User.state != "archived")
        .options(sa_orm.selectinload(models2.User.team))
        .options(sa_orm.selectinload(models2.User.remotecis))
    )
    query = d.handle_args(query, models2.User, args)
    count_query = select(func.count()).select_from(query.subquery())
    nb_users = flask.g.session.execute(count_query).scalar()
    query = d.handle_pagination(query, args)
    users = flask.g.session.execute(query).scalars().all()
    users = list(
        map(
            lambda u: u.serialize(only_columns=models2.User.api_fields),
            users,
        )
    )

    return flask.jsonify({"users": users, "_meta": {"count": nb_users}})


def user_by_id(user, user_id):
    if user.id != user_id and user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()
    base.get_resource_orm(models2.User, user_id)

    query = (
        select(models2.User)
        .where(models2.User.state != "archived")
        .where(models2.User.id == user_id)
        .options(sa_orm.selectinload(models2.User.team))
        .options(sa_orm.selectinload(models2.User.remotecis))
    )
    u = flask.g.session.execute(query).scalar_one()
    if not u:
        raise dci_exc.DCIException(message="user not found", status_code=404)

    return flask.Response(
        json.dumps({"user": u.serialize(only_columns=models2.User.api_fields)}),
        200,
        headers={"ETag": u.etag},
        content_type="application/json",
    )


@api.route("/users/<uuid:user_id>", methods=["GET"])
@decorators.login_required
def get_user_by_id(user, user_id):
    return user_by_id(user, str(user_id))


@api.route("/users/me", methods=["GET"])
@decorators.login_required
def get_current_user(user):
    return user_by_id(user, user.id)


@api.route("/users/me", methods=["PUT"])
@decorators.login_required
def put_current_user(user):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_current_user_schema, flask.request.json)

    if user.is_not_read_only_user():
        current_password = values["current_password"]
        encrypted_password = user.password
        if not auth.check_passwords_equal(current_password, encrypted_password):
            raise dci_exc.DCIException("current_password invalid")

    new_values = {}
    new_password = values.get("new_password")
    if new_password:
        encrypted_password = auth.hash_password(new_password)
        new_values["password"] = encrypted_password

    etag = utils.gen_etag()
    new_values.update(
        {
            "etag": etag,
            "fullname": values.get("fullname") or user.fullname,
            "email": values.get("email") or user.email,
            "timezone": values.get("timezone") or user.timezone,
        }
    )

    query = (
        update(models2.User)
        .where(models2.User.id == user.id)
        .where(models2.User.etag == if_match_etag)
        .values(new_values)
    )
    result = flask.g.session.execute(query)
    flask.g.session.commit()

    if result.rowcount == 0:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="update failed, either user not found or etag not matched",
            status_code=409,
        )

    query = select(models2.User).where(models2.User.id == user.id)
    u = flask.g.session.execute(query).scalar_one()
    if not u:
        raise dci_exc.DCIException(message="unable to return user", status_code=400)

    return flask.Response(
        json.dumps({"user": u.serialize(only_columns=models2.User.api_fields)}),
        200,
        headers={"ETag": etag},
        content_type="application/json",
    )


@api.route("/users/<uuid:user_id>", methods=["PUT"])
@decorators.login_required
def put_user(user, user_id):
    values = clean_json_with_schema(update_user_schema, flask.request.json)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    # to update a user the caller must be a super admin
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    values["etag"] = utils.gen_etag()

    password = values.pop("password", None)
    if password:
        values["password"] = auth.hash_password(password)

    query = (
        update(models2.User)
        .where(models2.User.id == user_id)
        .where(models2.User.etag == if_match_etag)
        .values(values)
    )
    result = flask.g.session.execute(query)
    flask.g.session.commit()

    if result.rowcount == 0:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="update failed, either user not found or etag not matched",
            status_code=409,
        )

    query = select(models2.User).where(models2.User.id == user_id)
    u = flask.g.session.execute(query).scalar_one()
    if not u:
        raise dci_exc.DCIException(message="unable to return user", status_code=400)

    return flask.Response(
        json.dumps({"user": u.serialize(only_columns=models2.User.api_fields)}),
        200,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/users/<uuid:user_id>", methods=["DELETE"])
@decorators.login_required
def delete_user_by_id(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    base.get_resource_orm(models2.User, user_id)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    query = (
        update(models2.User)
        .where(models2.User.id == user_id)
        .where(models2.User.etag == if_match_etag)
        .values({"state": "archived"})
    )
    result = flask.g.session.execute(query)
    flask.g.session.commit()

    if result.rowcount == 0:
        raise dci_exc.DCIException(
            message="delete failed, either user already deleted or etag not matched",
            status_code=409,
        )

    return flask.Response(None, 204, content_type="application/json")


@api.route("/users/<uuid:user_id>/remotecis", methods=["GET"])
@decorators.login_required
def get_subscribed_remotecis(identity, user_id):
    if (
        identity.is_not_super_admin()
        and identity.id != str(user_id)
        and identity.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    query = (
        select(models2.User)
        .where(models2.User.id == user_id)
        .where(models2.User.state != "archived")
        .options(sa_orm.selectinload(models2.User.remotecis))
    )
    user = flask.g.session.execute(query).scalar_one()
    user = user.serialize(only_columns=models2.User.api_fields)

    return flask.Response(
        json.dumps({"remotecis": user.get("remotecis")}),
        200,
        content_type="application/json",
    )


@api.route("/users/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_users(user):
    return base.get_to_purge_archived_resources(user, models2.User)


@api.route("/users/purge", methods=["POST"])
@decorators.login_required
def purge_archived_users(user):
    return base.purge_archived_resources(user, models2.User)
