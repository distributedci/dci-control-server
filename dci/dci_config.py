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

import os
import sys

from dci.db import models
from dci.stores import swift

import flask
import sqlalchemy


def generate_conf():
    conf = flask.Config('')
    conf.from_object('dci.settings')
    conf.from_object(os.environ.get('DCI_SETTINGS_MODULE'))
    return conf


def get_engine(conf):
    sa_engine = sqlalchemy.create_engine(
        conf['SQLALCHEMY_DATABASE_URI'],
        pool_size=conf['SQLALCHEMY_POOL_SIZE'],
        max_overflow=conf['SQLALCHEMY_MAX_OVERFLOW'],
        encoding='utf8',
        convert_unicode=conf['SQLALCHEMY_NATIVE_UNICODE'],
        echo=conf['SQLALCHEMY_ECHO'])
    return sa_engine


def get_store(container):
    conf = generate_conf()
    configuration = {
        'os_username': conf['STORE_USERNAME'],
        'os_password': conf['STORE_PASSWORD'],
        'os_tenant_name': conf['STORE_TENANT_NAME'],
        'os_auth_url': conf['STORE_AUTH_URL'],
    }
    if container == 'files':
        configuration['container'] = conf['STORE_FILES_CONTAINER']
    elif container == 'components':
        configuration['container'] = conf['STORE_COMPONENTS_CONTAINER']
    stores_engine = swift.Swift(configuration)
    return stores_engine


def sanity_check(conf):
    query_team_admin_id = sqlalchemy.sql.select([models.TEAMS]).where(
        models.TEAMS.c.name == 'admin')

    db_conn = get_engine(conf).connect()
    row = db_conn.execute(query_team_admin_id).fetchone()
    db_conn.close()

    if row is None:
        print("Admin team not found. Please init the database"
              " with the 'admin' team and 'admin' user.")
        sys.exit(1)
