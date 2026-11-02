# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci.db import models2
from tests import utils


def test_create_access_and_refresh_tokens(app):
    user_client = utils.generate_client(app)
    assert user_client.get("/api/v1/identity").status_code == 401
    data = {
        "email": "user1@example.org",
        "password": "user1",
    }
    response = user_client.post(
        "/api/v1/auth/login",
        json=data,
    )
    assert response.status_code == 201
    tokens = response.data
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    access_token = tokens["access_token"]
    response = user_client.get(
        "/api/v1/identity",
        headers={"Authorization": f"JWTBearer {access_token}"},
    )
    assert response.status_code == 200


def test_bad_password_return_401(app):
    user_client = utils.generate_client(app)
    data = {
        "email": "user1@example.org",
        "password": "bad password",
    }
    response = user_client.post(
        "/api/v1/auth/login",
        json=data,
    )
    assert response.status_code == 401
    assert response.data == {"msg": "Bad email or password"}


def test_refresh_token(app):
    user_client = utils.generate_client(app)
    data = {
        "email": "user1@example.org",
        "password": "user1",
    }
    response = user_client.post(
        "/api/v1/auth/login",
        json=data,
    )
    assert response.status_code == 201
    tokens = response.data
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    access_token = tokens["access_token"]
    response = user_client.get(
        "/api/v1/identity",
        headers={"Authorization": f"JWTBearer {access_token}"},
    )
    assert response.status_code == 200

    # Trying to refresh with access token should fail
    response = user_client.post(
        "/api/v1/auth/refresh",
        json={},
        headers={"Authorization": f"JWTBearer {access_token}"},
    )
    assert response.status_code == 422

    # Refreshing with refresh token should succeed
    refresh_token = tokens["refresh_token"]
    response = user_client.post(
        "/api/v1/auth/refresh",
        json={},
        headers={"Authorization": f"JWTBearer {refresh_token}"},
    )
    assert response.status_code == 200
    new_access_token = response.data["access_token"]
    assert new_access_token != access_token

    # New access token should work
    response = user_client.get(
        "/api/v1/identity",
        headers={"Authorization": f"JWTBearer {new_access_token}"},
    )
    assert response.status_code == 200


def test_user_with_empty_password_cannot_create_jwt_token(session, app):
    session.add(
        models2.User(
            name="nopassword@example.org",
            sso_username="nopassword@example.org",
            fullname="nopassword@example.org",
            password="",
            email="nopassword@example.org",
        )
    )
    session.commit()
    user_client = utils.generate_client(app)
    assert user_client.get("/api/v1/identity").status_code == 401
    data = {
        "email": "nopassword@example.org",
        "password": "",
    }
    response = user_client.post(
        "/api/v1/auth/login",
        json=data,
    )
    assert response.status_code == 400


def test_user_with_no_password_cannot_create_jwt_token(session, app):
    session.add(
        models2.User(
            name="nopassword@example.org",
            sso_username="nopassword@example.org",
            fullname="nopassword@example.org",
            password=None,
            email="nopassword@example.org",
        )
    )
    session.commit()
    user_client = utils.generate_client(app)
    assert user_client.get("/api/v1/identity").status_code == 401
    data = {
        "email": "nopassword@example.org",
        "password": None,
    }
    response = user_client.post(
        "/api/v1/auth/login",
        json=data,
    )
    assert response.status_code == 400
