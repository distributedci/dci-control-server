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

import json
from functools import wraps

import flask

from dci.auth import UNAUTHORIZED
import dci.auth_mechanism as am
from dci.common import exceptions as dci_exc
from dciauth import signature


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = ('Could not verify your access level for that URL.'
                    'Please login with proper credentials.')
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def _get_auth_class_from_headers(headers):
    if 'DCI-Auth-Signature' in headers:
        return am.SignatureAuthMechanism

    if 'Authorization' not in headers:
        raise dci_exc.DCIException('Authorization header missing',
                                   status_code=401)

    auth_header = headers.get('Authorization').split(' ')
    if len(auth_header) != 2:
        raise dci_exc.DCIException('Authorization header malformed',
                                   status_code=401)
    auth_type, token = auth_header
    if auth_type == 'Bearer':
        return am.OpenIDCAuth
    elif auth_type == signature.DCI_ALGORITHM:
        return am.HmacMechanism
    elif auth_type == 'Basic':
        return am.BasicAuthMechanism

    raise dci_exc.DCIException('Authorization scheme %s unknown' % auth_type,
                               status_code=401)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        flask.request.headers.get('DCI-Auth-Signature')
        auth_class = _get_auth_class_from_headers(flask.request.headers)
        auth_scheme = auth_class(flask.request)
        auth_scheme.authenticate()
        return f(auth_scheme.identity, *args, **kwargs)

    return decorated


def has_role(role_labels):
    """Decorator to ensure authentified entity has proper permission."""

    def actual_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = args[0]
            if user.role_label in role_labels:
                return f(*args, **kwargs)
            raise UNAUTHORIZED
        return wrapper
    return actual_decorator
