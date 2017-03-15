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
from functools import wraps
import hashlib
import hmac
import json
from passlib.apps import custom_app_context as pwd_context
import sqlalchemy.sql

from dci.common import exceptions as exc
from dci.db import models

UNAUTHORIZED = exc.DCIException('Operation not authorized.', status_code=401)

AUTH_BASIC = 'auth_basic'
AUTH_TOKEN = 'auth_token'
allowed_auth_types = set([AUTH_BASIC, AUTH_TOKEN])


def hash_password(password):
    return pwd_context.encrypt(password)


def build_auth(username, password):
    """Check the combination username/password that is valid on the
    database.
    """
    t_j = sqlalchemy.join(
        models.USERS, models.TEAMS,
        models.USERS.c.team_id == models.TEAMS.c.id)
    query_get_user = (sqlalchemy.sql
                      .select([
                          models.USERS,
                          models.TEAMS.c.name.label('team_name'),
                          models.TEAMS.c.country.label('team_country'),
                      ])
                      .select_from(t_j)
                      .where(models.USERS.c.name == username))

    user = flask.g.db_conn.execute(query_get_user).fetchone()
    if user is None:
        return None, False
    user = dict(user)

    return user, pwd_context.verify(password, user.get('password'))


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = ('Could not verify your access level for that URL.'
                    'Please login with proper credentials.')
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def is_admin(user, super=False):
    if super and user['role'] != 'admin':
        return False
    return user['team_name'] == 'admin'


def is_admin_user(user, team_id):
    return user['team_id'] == team_id and user['role'] == 'admin'


def is_in_team(user, team_id):
    return user['team_id'] == team_id


def check_export_control(user, component):
    if not is_admin(user):
        if not component['export_control']:
            raise UNAUTHORIZED


def reject_signature(reason):
    """Sends a 401 reject response which asks for an auth token."""

    auth_message = ('Could not grant access for that URL. Reason:\n%s' %
                    reason)
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'X-Auth-Signature required.'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def _get_remoteci(ci_id):
    """Get the CI API secret
    """
    query = sqlalchemy\
        .select([models.REMOTECIS])\
        .select_from(models.REMOTECIS)\
        .where(models.REMOTECIS.c.id == ci_id)
    remoteci = flask.g.db_conn.execute(query).fetchone()
    return remoteci


def _verify_remoteci_auth_signature(remoteci_id, auth_signature):
    if remoteci_id is None:
        return reject_signature('Required parameter remoteci_id missing')

    remoteci = _get_remoteci(remoteci_id)
    if remoteci is None:
        return None, False

    if remoteci.api_secret is None:
        return remoteci, False

    local_digest = _digest_request(
        remoteci.api_secret,
        flask.request).hexdigest()
    flask.current_app.logger.debug('Digest was: %s' % local_digest)
    # NOTE(fc): hmac.compare_digest available in python≥(2.7,3.3)
    compare_digest = getattr(hmac, 'compare_digest',
                             lambda a, b: a == b)
    return remoteci, compare_digest(auth_signature, local_digest)


def _digest_request(secret, request):
    h = hmac.new(secret.encode(), digestmod=hashlib.sha256)
    h.update(request.url.encode(request.charset or 'utf-8'))
    h.update(request.data.encode(request.charset or 'utf-8'))
    return h


def requires_auth(allow):
    # allow in dci.auth.allowed_auth_types
    # FIXME(fc): add doc about what's allowed
    def for_parameters(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if type(allow) is not set or len(allow) == 0:
                return reject('No authentication type requested')

            if len(allow - allowed_auth_types) != 0:
                return reject('Invalid authentication type requested')

            if AUTH_TOKEN in allow:
                request_digest = flask.request.headers.get('X-Auth-Signature')
                flask.current_app.logger.debug('X-Auth-Signature: %s' %
                                               request_digest)

                remaining_auth_types = allow - {AUTH_TOKEN}
                if request_digest is None and len(remaining_auth_types) == 0:
                    return reject_signature(
                        'Required X-Auth-Signature header not found.')

                remoteci_id = flask.request.values.get('remoteci_id')
                flask.current_app.logger.debug('Requested remoteci_id: %s' %
                                               remoteci_id)
                remoteci, auth_ok = _verify_remoteci_auth_signature(
                    remoteci_id,
                    request_digest)
                if not auth_ok:
                    return reject('Signature could not be verified: %s' %
                                  request_digest)

                return func(None, remoteci=remoteci, *args, **kwargs)

            if AUTH_BASIC in allow:
                auth = flask.request.authorization
                if not auth:
                    return reject()
                user, is_authenticated = build_auth(auth.username,
                                                    auth.password)
                if not is_authenticated:
                    return reject()
                return func(user, *args, **kwargs)
        return decorated
    return for_parameters
