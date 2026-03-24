# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

from sqlalchemy import exc as sa_exc, select, update, func
import sqlalchemy.orm as sa_orm
from sqlalchemy import sql

from dci import decorators
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_product_schema,
    update_product_schema,
    add_team_to_product_schema,
    check_and_get_args,
)
from dci.common import utils
from dci.db import declarative as d
from dci.db import models2


@api.route("/products", methods=["POST"])
@decorators.login_required
@decorators.log
def create_product(user):
    values = flask.request.json
    check_json_is_valid(create_product_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    if not values["label"]:
        values.update({"label": values["name"].upper()})

    p_serialized = base.create_resource_orm(models2.Product, values)

    return flask.Response(
        json.dumps({"product": p_serialized}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/products/<uuid:product_id>", methods=["PUT"])
@decorators.login_required
def update_product(user, product_id):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_product_schema, flask.request.json)
    values["etag"] = utils.gen_etag()
    if "label" in values:
        values["label"] = values["label"].upper()

    # get and update resource
    product = base.get_resource_orm(models2.Product, product_id, if_match_etag)
    base.update_resource_orm(product, values)
    product = base.get_resource_orm(models2.Product, product_id)

    return flask.Response(
        json.dumps(
            {"product": product.serialize(only_columns=models2.Product.api_fields)}
        ),
        200,
        headers={"ETag": product.etag},
        content_type="application/json",
    )


@api.route("/products", methods=["GET"])
@decorators.login_required
def get_all_products(user):
    args = check_and_get_args(flask.request.args.to_dict())

    query = (
        select(models2.Product)
        .where(models2.Product.state != "archived")
        .options(sa_orm.selectinload(models2.Product.topics))
    )
    query = d.handle_args(query, models2.Product, args)

    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        _JPT = models2.JOIN_PRODUCTS_TEAMS
        query = query.join(
            _JPT,
            sql.and_(
                _JPT.c.product_id == models2.Product.id,
                _JPT.c.team_id.in_(user.teams_ids),
            ),
        )
    query = query.distinct()
    count_query = select(func.count()).select_from(query.subquery())
    nb_products = flask.g.session.execute(count_query).scalar()
    query = d.handle_pagination(query, args)
    products = flask.g.session.execute(query).scalars().all()
    products = list(
        map(lambda p: p.serialize(only_columns=models2.Product.api_fields), products)
    )

    return flask.jsonify({"products": products, "_meta": {"count": nb_products}})


@api.route("/products/<uuid:product_id>", methods=["GET"])
@decorators.login_required
def get_product_by_id(user, product_id):
    try:
        query = (
            select(models2.Product)
            .where(models2.Product.state != "archived")
            .where(models2.Product.id == product_id)
            .options(sa_orm.selectinload(models2.Product.topics))
        )
        if (
            user.is_not_super_admin()
            and user.is_not_read_only_user()
            and user.is_not_epm()
        ):
            _JPT = models2.JOIN_PRODUCTS_TEAMS
            query = query.join(
                _JPT,
                sql.and_(
                    _JPT.c.product_id == models2.Product.id,
                    _JPT.c.team_id.in_(user.teams_ids),
                ),
            )
        p = flask.g.session.execute(query).scalar_one()
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="product not found", status_code=404)

    return flask.Response(
        json.dumps({"product": p.serialize(only_columns=models2.Product.api_fields)}),
        200,
        headers={"ETag": p.etag},
        content_type="application/json",
    )


@api.route("/products/<uuid:product_id>", methods=["DELETE"])
@decorators.login_required
def delete_product_by_id(user, product_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    base.get_resource_orm(models2.Product, product_id)

    query = (
        update(models2.Product)
        .where(models2.Product.id == product_id)
        .where(models2.Product.etag == if_match_etag)
        .values({"state": "archived"})
    )
    result = flask.g.session.execute(query)
    flask.g.session.commit()

    if result.rowcount == 0:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="delete failed, check etag", status_code=409)

    return flask.Response(None, 204, content_type="application/json")


@api.route("/products/<uuid:product_id>/teams", methods=["POST"])
@decorators.login_required
def add_team_to_product(user, product_id):
    values = flask.request.json
    check_json_is_valid(add_team_to_product_schema, values)

    team_id = values.get("team_id")

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        query_product = (
            select(models2.Product)
            .where(models2.Product.state != "archived")
            .where(models2.Product.id == product_id)
        )
        p = flask.g.session.execute(query_product).scalar_one()
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="product not found", status_code=404)

    try:
        query_team = (
            select(models2.Team)
            .where(models2.Team.state != "archived")
            .where(models2.Team.id == team_id)
        )
        t = flask.g.session.execute(query_team).scalar_one()
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="team not found", status_code=404)

    if t not in p.teams:
        try:
            p.teams.append(t)
            flask.g.session.add(p)
            flask.g.session.commit()
        except sa_exc.IntegrityError:
            flask.g.session.rollback()
            raise dci_exc.DCIException(
                message="conflict when adding team", status_code=409
            )

    result = json.dumps({"product_id": p.id, "team_id": t.id})
    return flask.Response(result, 201, content_type="application/json")


@api.route("/products/<uuid:product_id>/teams/<uuid:team_id>", methods=["DELETE"])
@decorators.login_required
def delete_team_from_product(user, product_id, team_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        query_product = (
            select(models2.Product)
            .where(models2.Product.state != "archived")
            .where(models2.Product.id == product_id)
        )
        p = flask.g.session.execute(query_product).scalar_one()
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="product not found", status_code=404)

    try:
        query_team = (
            select(models2.Team)
            .where(models2.Team.state != "archived")
            .where(models2.Team.id == team_id)
        )
        t = flask.g.session.execute(query_team).scalar_one()
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="team not found", status_code=404)

    try:
        p.teams.remove(t)
        flask.g.session.add(p)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="conflict when removing team", status_code=409
        )

    return flask.Response(None, 204, content_type="application/json")


# this is already provided by GET /products/<uuid:product_id> and will be removed
@api.route("/products/<uuid:product_id>/teams", methods=["GET"])
@decorators.login_required
def get_all_teams_from_product(user, product_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    query = (
        select(models2.Team)
        .where(models2.Team.state != "archived")
        .join(models2.Team.products)
        .where(models2.Product.id == product_id)
        .where(models2.Product.state != "archived")
    )
    teams = [
        t.serialize(only_columns=models2.Team.api_fields)
        for t in flask.g.session.execute(query).scalars().all()
    ]

    return flask.jsonify({"teams": teams, "_meta": {"count": len(teams)}})


@api.route("/products/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_products(user):
    return base.get_to_purge_archived_resources(user, models2.Product)


@api.route("/products/purge", methods=["POST"])
@decorators.login_required
def purge_archived_products(user):
    return base.purge_archived_resources(user, models2.Product)
