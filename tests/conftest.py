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

import dci.app
from dci.db import models
from dci.elasticsearch import engine as es_engine
import tests.utils as utils

from passlib.apps import custom_app_context as pwd_context
import pytest
import sqlalchemy
import sqlalchemy_utils.functions


@pytest.fixture(scope='session')
def engine(request):
    utils.rm_upload_folder()
    db_uri = utils.conf['SQLALCHEMY_DATABASE_URI']

    engine = sqlalchemy.create_engine(db_uri)

    def del_db():
        if sqlalchemy_utils.functions.database_exists(db_uri):
            sqlalchemy_utils.functions.drop_database(db_uri)

    del_db()
    request.addfinalizer(del_db)
    sqlalchemy_utils.functions.create_database(db_uri)

    models.metadata.create_all(engine)
    return engine


@pytest.fixture
def clean_all(request, engine):
    models.metadata.drop_all(engine)
    request.addfinalizer(lambda: models.metadata.create_all(engine))


@pytest.fixture(scope='session', autouse=True)
def memoize_password_hash():
    pwd_context.verify = utils.memoized(pwd_context.verify)
    pwd_context.encrypt = utils.memoized(pwd_context.encrypt)


@pytest.fixture
def db_clean(request, engine):
    def fin():
        for table in reversed(models.metadata.sorted_tables):
            engine.execute(table.delete())
    request.addfinalizer(fin)


@pytest.fixture
def fs_clean(request):
    """Clean test file upload directory"""
    request.addfinalizer(utils.rm_upload_folder)


@pytest.fixture
def db_provisioning(db_clean, engine):
    with engine.begin() as conn:
        utils.provision(conn)


@pytest.fixture
def app(db_provisioning, engine, es_clean, fs_clean):
    app = dci.app.create_app(utils.conf)
    app.testing = True
    app.engine = engine
    return app


@pytest.fixture
def admin(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'admin'))


@pytest.fixture
def unauthorized(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'bob'))


@pytest.fixture
def user(app, db_provisioning):
    return utils.generate_client(app, ('user', 'user'))


@pytest.fixture
def user_admin(app, db_provisioning):
    return utils.generate_client(app, ('user_admin', 'user_admin'))


@pytest.fixture
def topic_id(admin, team_admin_id):
    data = {'name': 'topic_name'}
    topic = admin.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % t_id,
               data={'team_id': team_admin_id})
    return t_id


@pytest.fixture
def test_id(admin, topic_id):
    data = {'name': 'pname', 'topic_id': topic_id}
    test = admin.post('/api/v1/tests', data=data).data
    return test['test']['id']


@pytest.fixture
def team_id(admin):
    team = admin.post('/api/v1/teams', data={'name': 'pname'}).data
    return team['team']['id']


@pytest.fixture
def team_user_id(admin):
    team = admin.get('/api/v1/teams/user').data
    return team['team']['id']


@pytest.fixture
def team_admin_id(admin):
    team = admin.get('/api/v1/teams/admin').data
    return team['team']['id']


@pytest.fixture
def topic_user_id(admin, user, team_user_id):
    data = {'name': 'topic_user_name'}
    topic = admin.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % t_id,
               data={'team_id': team_user_id})
    return t_id


@pytest.fixture
def remoteci_id(admin, team_id):
    data = {'name': 'pname', 'team_id': team_id}
    remoteci = admin.post('/api/v1/remotecis', data=data).data
    return remoteci['remoteci']['id']


@pytest.fixture
def remoteci_user_id(user, team_user_id):
    data = {'name': 'rname', 'team_id': team_user_id}
    remoteci = user.post('/api/v1/remotecis', data=data).data
    return remoteci['remoteci']['id']


@pytest.fixture
def jobdefinition_factory(admin, topic_id):
    def create(name='pname', topic_id=topic_id):
        data = {'name': name, 'topic_id': topic_id}
        jd = admin.post('/api/v1/jobdefinitions', data=data).data
        return jd
    return create


@pytest.fixture
def jobdefinition_id(jobdefinition_factory):
    jd = jobdefinition_factory()
    return jd['jobdefinition']['id']


@pytest.fixture
def jobdefinition_user_id(jobdefinition_factory, topic_user_id):
    return jobdefinition_factory(topic_id=topic_user_id)


@pytest.fixture
def job_id(admin, jobdefinition_id, team_id, remoteci_id):
    data = {'jobdefinition_id': jobdefinition_id, 'team_id': team_id,
            'remoteci_id': remoteci_id}
    job = admin.post('/api/v1/jobs', data=data).data
    return job['job']['id']


@pytest.fixture
def job_user_id(admin, jobdefinition_id, team_user_id, remoteci_user_id):
    data = {'jobdefinition_id': jobdefinition_id, 'team_id': team_user_id,
            'remoteci_id': remoteci_user_id}
    job = admin.post('/api/v1/jobs', data=data).data
    return job['job']['id']


@pytest.fixture
def jobstate_id(admin, job_id):
    data = {'job_id': job_id, 'status': 'running',
            'comment': 'kikoolol'}
    jobstate = admin.post('/api/v1/jobstates', data=data).data
    return jobstate['jobstate']['id']


@pytest.fixture
def jobstate_user_id(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol'}
    jobstate = user.post('/api/v1/jobstates', data=data).data
    return jobstate['jobstate']['id']


@pytest.fixture
def file_id(admin, jobstate_id, team_admin_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_id,
               'DCI-NAME': 'name'}
    file = admin.post('/api/v1/files', headers=headers, data='kikoolol').data
    headers['team_id'] = team_admin_id
    headers['id'] = file['file']['id']
    conn = es_engine.DCIESEngine(utils.conf)
    conn.index(headers)
    return file['file']['id']


@pytest.fixture
def file_user_id(user, jobstate_user_id, team_user_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
               'DCI-NAME': 'name'}
    file = user.post('/api/v1/files', headers=headers, data='kikoolol').data
    headers['team_id'] = team_user_id
    headers['id'] = file['file']['id']
    conn = es_engine.DCIESEngine(utils.conf)
    conn.index(headers)
    return file['file']['id']


@pytest.fixture
def file_job_user_id(user, job_id, team_user_id):
    headers = {'DCI-JOB-ID': job_id,
               'DCI-NAME': 'name'}
    file = user.post('/api/v1/files', headers=headers, data='foobar').data
    headers['team_id'] = team_user_id
    headers['id'] = file['file']['id']
    conn = es_engine.DCIESEngine(utils.conf)
    conn.index(headers)
    return file['file']['id']


@pytest.fixture
def es_clean(request):
    conn = es_engine.DCIESEngine(utils.conf)
    conn.cleanup()
