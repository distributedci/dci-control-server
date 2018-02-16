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

import datetime

import dci.auth_mechanism as authm
from dci.common import exceptions as dci_exc

import flask
import mock
import pytest


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_verified(m_datetime, admin, app, engine, access_token):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    sso_headers = mock.Mock
    sso_headers.headers = {'Authorization': 'Bearer %s' % access_token}
    nb_users = len(admin.get('/api/v1/users').data['users'])
    with app.app_context():
        flask.g.db_conn = engine.connect()
        mech = authm.OpenIDCAuth(sso_headers)
        mech.authenticate()
        assert mech.identity['team_id'] is None
        assert mech.identity['name'] == 'dci'
        assert mech.identity['sso_username'] == 'dci'
        assert mech.identity['email'] == 'dci@distributed-ci.io'
        nb_users_after_sso = len(admin.get('/api/v1/users').data['users'])
        assert (nb_users + 1) == nb_users_after_sso


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_not_verified(m_datetime, admin, app, engine, access_token):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    # corrupt access_token
    access_token = access_token + 'lol'
    sso_headers = mock.Mock
    sso_headers.headers = {'Authorization': 'Bearer %s' % access_token}
    nb_users = len(admin.get('/api/v1/users').data['users'])
    with app.app_context():
        flask.g.db_conn = engine.connect()
        mech = authm.OpenIDCAuth(sso_headers)
        with pytest.raises(dci_exc.DCIException):
            mech.authenticate()
        assert mech.identity is None
        nb_users_after_sso = len(admin.get('/api/v1/users').data['users'])
        assert nb_users == nb_users_after_sso


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_get_users(m_datetime, user_sso, app, engine):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.db_conn = engine.connect()
        gusers = user_sso.get('/api/v1/users')
        assert gusers.status_code == 200


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_get_current_user(m_datetime, user_sso, app, engine):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.db_conn = engine.connect()
        request = user_sso.get('/api/v1/users/me?embed=team,role,remotecis')
        assert request.status_code == 200
