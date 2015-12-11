# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

from dci.server import auth
from dci.server.db import models

user_pw_hash = auth.hash_password('user')
user_admin_pw_hash = auth.hash_password('user_admin')
admin_pw_hash = auth.hash_password('admin')


def provision(db_conn):
    def db_insert(model_item, **kwargs):
        query = model_item.insert().values(**kwargs)
        return db_conn.execute(query).inserted_primary_key[0]

    # Create teams
    team_admin_id = db_insert(models.TEAMS, name='admin')
    team_user_id = db_insert(models.TEAMS, name='user')

    # Create users
    db_insert(models.USERS,
              name='user',
              role='user',
              password=user_pw_hash,
              team_id=team_user_id)

    db_insert(models.USERS,
              name='user_admin',
              role='admin',
              password=user_admin_pw_hash,
              team_id=team_user_id)

    db_insert(models.USERS,
              name='admin',
              role='admin',
              password=admin_pw_hash,
              team_id=team_admin_id)
