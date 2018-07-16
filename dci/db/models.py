# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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

import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy_utils as sa_utils

from dci.common import signature, utils

metadata = sa.MetaData()

JOB_STATUSES = ['new', 'pre-run', 'running', 'post-run',
                'success', 'failure', 'killed', 'error']
STATUSES = sa.Enum(*JOB_STATUSES, name='statuses')
FINAL_STATUSES = ['success', 'failure', 'error']
FINAL_STATUSES_ENUM = sa.Enum(*FINAL_STATUSES, name='final_statuses')

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

ISSUE_TRACKERS = ['github', 'bugzilla']
TRACKERS = sa.Enum(*ISSUE_TRACKERS, name='trackers')


COMPONENTS = sa.Table(
    'components', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('type', sa.String(255), nullable=False),
    sa.Column('canonical_project_name', sa.String),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('title', sa.Text),
    sa.Column('message', sa.Text),
    sa.Column('url', sa.Text),
    sa.Column('export_control', sa.BOOLEAN, nullable=False, default=False),
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('active_components_name_topic_id_key',
             'name', 'topic_id',
             unique=True,
             postgresql_where=sa.sql.text("components.state = 'active'")),
    sa.Index('components_topic_id_idx', 'topic_id'),
    sa.Column('state', STATES, default='active')
)


JOIN_COMPONENTS_ISSUES = sa.Table(
    'components_issues', metadata,
    sa.Column('component_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('components.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('issue_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('issues.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('users.id'),
              nullable=False),
    sa.Index('components_issues_user_id_idx', 'user_id'))


TOPICS = sa.Table(
    'topics', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), unique=True, nullable=False),
    sa.Column('label', sa.Text),
    sa.Column('component_types', pg.JSON, default=[]),
    sa.Column('product_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('products.id'),
              nullable=True),
    sa.Column('next_topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id'),
              nullable=True, default=None),
    sa.Index('topics_product_id_idx', 'product_id'),
    sa.Index('topics_next_topic_id_idx', 'next_topic_id'),
    sa.Column('state', STATES, default='active'),
    sa.Column('data', sa_utils.JSONType, default={})
)

JOINS_TOPICS_TEAMS = sa.Table(
    'topics_teams', metadata,
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

TESTS = sa.Table(
    'tests', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('tests_team_id_idx', 'team_id'),
    sa.Column('state', STATES, default='active'),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
)

JOIN_REMOTECIS_TESTS = sa.Table(
    'remoteci_tests', metadata,
    sa.Column('remoteci_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('test_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('tests.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

JOIN_TOPICS_TESTS = sa.Table(
    'topic_tests', metadata,
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('test_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('tests.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

TEAMS = sa.Table(
    'teams', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    # https://en.wikipedia.org/wiki/ISO_3166-1 Alpha-2 code
    sa.Column('country', sa.String(255), nullable=True),
    sa.Column('state', STATES, default='active'),
    sa.Column('external', sa.BOOLEAN, default=True),
    sa.Column('parent_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='SET NULL'),
              nullable=True),
    sa.UniqueConstraint('name', 'parent_id', name='teams_name_parent_id_key')
)


REMOTECIS = sa.Table(
    'remotecis', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('api_secret', sa.String(64), default=signature.gen_secret),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Column('role_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('roles.id', ondelete='SET NULL')),
    sa.Index('remotecis_team_id_idx', 'team_id'),
    sa.UniqueConstraint('name', 'team_id', name='remotecis_name_team_id_key'),
    sa.Column('public', sa.BOOLEAN, default=False),
    sa.Column('cert_fp', sa.String(255)),
    sa.Column('state', STATES, default='active')
)

JOBS = sa.Table(
    'jobs', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('comment', sa.Text),
    sa.Column('status', STATUSES, default='new'),
    sa.Column('rconfiguration_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('rconfigurations.id'),
              nullable=True),
    sa.Index('jobs_rconfiguration_id_idx', 'rconfiguration_id'),
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              # todo(yassine): nullable=False
              nullable=True),
    sa.Index('jobs_topic_id_idx', 'topic_id'),
    sa.Column('remoteci_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('jobs_remoteci_id_idx', 'remoteci_id'),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('jobs_team_id_idx', 'team_id'),
    sa.Column('user_agent', sa.String(255)),
    sa.Column('client_version', sa.String(255)),
    sa.Column('previous_job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id'),
              nullable=True, default=None),
    sa.Index('jobs_previous_job_id_idx', 'previous_job_id'),
    sa.Column('update_previous_job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id'),
              nullable=True, default=None),
    sa.Index('jobs_update_previous_job_id_idx', 'update_previous_job_id'),
    sa.Column('state', STATES, default='active')
)

TESTS_RESULTS = sa.Table(
    'tests_results', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('total', sa.Integer),
    sa.Column('success', sa.Integer),
    sa.Column('skips', sa.Integer),
    sa.Column('failures', sa.Integer),
    sa.Column('regressions', sa.Integer, default=0),
    sa.Column('errors', sa.Integer),
    sa.Column('time', sa.Integer),
    sa.Column('job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=False),
    sa.Column('tests_cases', pg.JSON, default=[]),
    sa.Index('tests_results_job_id_idx', 'job_id'),
    sa.Column('file_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('files.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('tests_results_file_id_idx', 'file_id')
)

METAS = sa.Table(
    'metas', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.Text),
    sa.Column('value', sa.Text),
    sa.Column('job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('metas_job_id_idx', 'job_id')
)

JOIN_JOBS_COMPONENTS = sa.Table(
    'jobs_components', metadata,
    sa.Column('job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('component_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('components.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

JOIN_JOBS_ISSUES = sa.Table(
    'jobs_issues', metadata,
    sa.Column('job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('issue_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('issues.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('users.id')),
    sa.Index('jobs_issues_user_id_idx', 'user_id')
)

JOBSTATES = sa.Table(
    'jobstates', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('status', STATUSES, nullable=False),
    sa.Column('comment', sa.Text),
    sa.Column('job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('jobstates_job_id_idx', 'job_id'),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('jobstates_team_id_idx', 'team_id')
)

JOIN_REMOTECIS_RCONFIGURATIONS = sa.Table(
    'remotecis_rconfigurations', metadata,
    sa.Column('remoteci_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('rconfiguration_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('rconfigurations.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

REMOTECIS_RCONFIGURATIONS = sa.Table(
    'rconfigurations', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('state', STATES, default='active'),
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('component_types', pg.JSON, nullable=True, default=None),
    sa.Column('data', sa_utils.JSONType),
    sa.Index('rconfigurations_topic_id_idx', 'topic_id')
)

FILES = sa.Table(
    'files', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('mime', sa.String),
    sa.Column('md5', sa.String(32)),
    sa.Column('size', sa.BIGINT, nullable=True),
    sa.Column('jobstate_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobstates.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('files_jobstate_id_idx', 'jobstate_id'),
    sa.Column('test_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('tests.id', ondelete='CASCADE'),
              nullable=True, default=None),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('files_team_id_idx', 'team_id'),
    sa.Column('job_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('files_job_id_idx', 'job_id'),
    sa.Column('state', STATES, default='active'),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag)
)

JOBS_EVENTS = sa.Table(
    'jobs_events', metadata,
    sa.Column('id', sa.Integer, primary_key=True,
              autoincrement=True),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('job_id', pg.UUID(as_uuid=True), nullable=False),
    sa.Column('topic_id', pg.UUID(as_uuid=True), nullable=False),
    sa.Column('status', FINAL_STATUSES_ENUM),
    sa.Index('jobs_events_job_id_idx', 'job_id')
)

COUNTER = sa.Table(
    'counter', metadata,
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), primary_key=True, nullable=False),
    sa.Column('sequence', sa.Integer, default=0),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag)
)

COMPONENT_FILES = sa.Table(
    'component_files', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('mime', sa.String),
    sa.Column('md5', sa.String(32)),
    sa.Column('size', sa.BIGINT, nullable=True),
    sa.Column('component_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('components.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('component_files_component_id_idx', 'component_id'),
    sa.Column('state', STATES, default='active'),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag)
)
COMPONENTFILES = COMPONENT_FILES.alias('componentfiles')

USERS = sa.Table(
    'users', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('sso_username', sa.String(255), nullable=True, unique=True),
    sa.Column('fullname', sa.String(255), nullable=False),
    sa.Column('email', sa.String(255), nullable=False, unique=True),
    sa.Column('password', sa.Text, nullable=True),
    sa.Column('timezone', sa.String(255), nullable=False, default='UTC'),
    sa.Column('role_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('roles.id', ondelete='SET NULL')),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('users_team_id_idx', 'team_id'),
    sa.Column('state', STATES, default='active')
)

JOIN_USER_REMOTECIS = sa.Table(
    'user_remotecis', metadata,
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('users.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('remoteci_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

LOGS = sa.Table(
    'logs', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('user_id', pg.UUID(as_uuid=True),
              nullable=False),
    sa.Index('logs_user_id_idx', 'user_id'),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('logs_team_id_idx', 'team_id'),
    sa.Column('action', sa.Text, nullable=False)
)

ISSUES = sa.Table(
    'issues', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('url', sa.Text, unique=True),
    sa.Column('tracker', TRACKERS, nullable=False)
)

ROLES = sa.Table(
    'roles', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('label', sa.String(255), nullable=False),
    sa.Column('description', sa.Text),
    sa.UniqueConstraint('label', name='roles_label_key'),
    sa.Column('state', STATES, default='active')
)

PERMISSIONS = sa.Table(
    'permissions', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('label', sa.String(255), nullable=False, unique=True),
    sa.Column('description', sa.Text),
    sa.Column('state', STATES, default='active')
)

JOIN_ROLES_PERMISSIONS = sa.Table(
    'roles_permissions', metadata,
    sa.Column('role_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('roles.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('permission_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('permissions.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)

PRODUCTS = sa.Table(
    'products', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('label', sa.String(255), nullable=False, unique=True),
    sa.Column('description', sa.Text),
    sa.Column('state', STATES, default='active'),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='SET NULL'),
              nullable=False))

FEEDERS = sa.Table(
    'feeders', metadata,
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('api_secret', sa.String(64), default=signature.gen_secret),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Column('role_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('roles.id', ondelete='SET NULL')),
    sa.Index('feeders_team_id_idx', 'team_id'),
    sa.UniqueConstraint('name', 'team_id', name='feeders_name_team_id_key'),
    sa.Column('state', STATES, default='active')
)
