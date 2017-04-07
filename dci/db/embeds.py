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

from dci.db import models

from sqlalchemy.sql import and_


def ignore_columns_from_table(table, ignored_columns):
    return [getattr(table.c, column.name)
            for column in table.columns
            if column.name not in ignored_columns]

# These functions should be called by v1_utils.QueryBuilder

# Create necessary aliases
JOBDEFINITION = models.JOBDEFINITIONS.alias('jobdefinition')

REMOTECI_TESTS = models.TESTS.alias('remoteci.tests')
JOBDEFINITION_TESTS = models.TESTS.alias('jobdefinition.tests')
TEAM = models.TEAMS.alias('team')
REMOTECI = models.REMOTECIS.alias('remoteci')
CFILES = models.COMPONENT_FILES.alias('files')

JOB = models.JOBS.alias('job')
JOB_WITHOUT_CONFIGURATION = ignore_columns_from_table(JOB, ['configuration'])  # noqa
JOBS_WITHOUT_CONFIGURATION = ignore_columns_from_table(models.JOBS, ['configuration'])  # noqa

LASTJOB = models.JOBS.alias('lastjob')
LASTJOB_WITHOUT_CONFIGURATION = ignore_columns_from_table(LASTJOB, ['configuration'])  # noqa
LASTJOB_COMPONENTS = models.COMPONENTS.alias('lastjob.components')
LASTJOB_JOIN_COMPONENTS = models.JOIN_JOBS_COMPONENTS.alias('lastjob.jobcomponents')  # noqa

CURRENTJOB = models.JOBS.alias('currentjob')
CURRENTJOB_WITHOUT_CONFIGURATION = ignore_columns_from_table(CURRENTJOB, ['configuration'])  # noqa
CURRENTJOB_COMPONENTS = models.COMPONENTS.alias('currentjob.components')
CURRENTJOB_JOIN_COMPONENTS = models.JOIN_JOBS_COMPONENTS.alias('currentjob.jobcomponents')  # noqa

JOBSTATE = models.JOBSTATES.alias('jobstate')
JOBSTATE_JOBS = models.JOBS.alias('jobstate.job')
JOBSTATEJOBS_WITHOUT_CONFIGURATION = ignore_columns_from_table(JOBSTATE_JOBS, ['configuration'])  # noqa

TOPIC = models.TOPICS.alias('topic')


def jobs(root_select=models.JOBS):
    return {
        'files': [
            {'right': models.FILES,
             'onclause': and_(models.FILES.c.job_id == root_select.c.id,
                              models.FILES.c.state != 'archived'),
             'isouter': True}],
        'metas': [
            {'right': models.METAS,
             'onclause': models.METAS.c.job_id == root_select.c.id,
             'isouter': True}],
        'jobdefinition': [
            {'right': JOBDEFINITION,
             'onclause': and_(root_select.c.jobdefinition_id == JOBDEFINITION.c.id,  # noqa
                              JOBDEFINITION.c.state != 'archived')}],
        'jobdefinition.tests': [
            {'right': models.JOIN_JOBDEFINITIONS_TESTS,
             'onclause': models.JOIN_JOBDEFINITIONS_TESTS.c.jobdefinition_id == JOBDEFINITION.c.id,  # noqa
             'isouter': True},
            {'right': JOBDEFINITION_TESTS,
             'onclause': and_(models.JOIN_JOBDEFINITIONS_TESTS.c.test_id == JOBDEFINITION_TESTS.c.id,  # noqa
                              JOBDEFINITION_TESTS.c.state != 'archived'),
             'isouter': True}],
        'remoteci': [
            {'right': REMOTECI,
             'onclause': and_(root_select.c.remoteci_id == REMOTECI.c.id,
                              REMOTECI.c.state != 'archived')}],
        'remoteci.tests': [
            {'right': models.JOIN_REMOTECIS_TESTS,
             'onclause': models.JOIN_REMOTECIS_TESTS.c.remoteci_id == REMOTECI.c.id,  # noqa
             'isouter': True},
            {'right': REMOTECI_TESTS,
             'onclause': and_(REMOTECI_TESTS.c.id == models.JOIN_REMOTECIS_TESTS.c.test_id,  # noqa
                              REMOTECI_TESTS.c.state != 'archived'),
             'isouter': True}],
        'components': [
            {'right': models.JOIN_JOBS_COMPONENTS,
             'onclause': models.JOIN_JOBS_COMPONENTS.c.job_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.COMPONENTS,
             'onclause': and_(models.COMPONENTS.c.id == models.JOIN_JOBS_COMPONENTS.c.component_id,  # noqa
                              models.COMPONENTS.c.state != 'archived'),
             'isouter': True}],
        'team': [
            {'right': TEAM,
             'onclause': and_(root_select.c.team_id == TEAM.c.id,
                              TEAM.c.state != 'archived')}]
    }


def remotecis(root_select=models.REMOTECIS):
    return {
        'team': [
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == root_select.c.team_id,
                              TEAM.c.state != 'archived')}
        ],
        'lastjob': [
            {'right': LASTJOB,
             'onclause': and_(
                 LASTJOB.c.state != 'archived',
                 LASTJOB.c.status.in_([
                     'success',
                     'failure',
                     'killed',
                     'product-failure',
                     'deployment-failure']),
                 LASTJOB.c.remoteci_id == root_select.c.id),
             'isouter': True,
             'sort': LASTJOB.c.created_at}],
        'lastjob.components': [
            {'right': LASTJOB_JOIN_COMPONENTS,
             'onclause': LASTJOB_JOIN_COMPONENTS.c.job_id == LASTJOB.c.id,  # noqa
             'isouter': True},
            {'right': LASTJOB_COMPONENTS,
             'onclause': and_(LASTJOB_COMPONENTS.c.id == LASTJOB_JOIN_COMPONENTS.c.component_id,  # noqa
                              LASTJOB_COMPONENTS.c.state != 'archived'),
             'isouter': True}],
        'currentjob': [
            {'right': CURRENTJOB,
             'onclause': and_(
                 CURRENTJOB.c.state != 'archived',
                 CURRENTJOB.c.status.in_([
                     'new',
                     'pre-run',
                     'running']),
                 CURRENTJOB.c.remoteci_id == root_select.c.id),
             'isouter': True,
             'sort': CURRENTJOB.c.created_at}],
        'currentjob.components': [
            {'right': CURRENTJOB_JOIN_COMPONENTS,
             'onclause': CURRENTJOB_JOIN_COMPONENTS.c.job_id == CURRENTJOB.c.id,  # noqa
             'isouter': True},
            {'right': CURRENTJOB_COMPONENTS,
             'onclause': and_(CURRENTJOB_COMPONENTS.c.id == CURRENTJOB_JOIN_COMPONENTS.c.component_id,  # noqa
                              CURRENTJOB_COMPONENTS.c.state != 'archived'),
             'isouter': True}]
    }


def components(root_select=models.COMPONENTS):
    return {
        'files': [
            {'right': CFILES,
             'onclause': and_(
                 CFILES.c.component_id == root_select.c.id,
                 CFILES.c.state != 'archived'),
             'isouter': True
             }],
        'jobs': [
            {'right': models.JOIN_JOBS_COMPONENTS,
             'onclause': models.JOIN_JOBS_COMPONENTS.c.component_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.JOBS,
             'onclause': and_(models.JOBS.c.id == models.JOIN_JOBS_COMPONENTS.c.job_id,  # noqa
                              models.JOBS.c.state != 'archived'),
             'isouter': True}]
    }


def files(root_select=models.FILES):
    return {
        'jobstate': [
            {'right': JOBSTATE,
             'onclause': JOBSTATE.c.id == root_select.c.jobstate_id,
             'isouter': True}
        ],
        'jobstate.job': [
            {'right': JOBSTATE_JOBS,
             'onclause': JOBSTATE.c.job_id == JOBSTATE_JOBS.c.id,
             'isouter': True}],
        'job': [
            {'right': JOB,
             'onclause': root_select.c.job_id == JOB.c.id,
             'isouter': True}
        ],
        'team': [
            {'right': TEAM,
             'onclause': root_select.c.team_id == TEAM.c.id}
        ]
    }


def jobdefinitions(root_select=models.JOBDEFINITIONS):
    return {
        'topic': [
            {'right': TOPIC,
             'onclause': root_select.c.topic_id == TOPIC.c.id}
        ]
    }


def jobstates(root_select=models.JOBSTATES):
    return {
        'files': [
            {'right': models.FILES,
             'onclause': and_(models.FILES.c.jobstate_id == root_select.c.id,
                              models.FILES.c.state != 'archived'),
             'isouter': True}],
        'job': [
            {'right': JOB,
             'onclause': root_select.c.job_id == JOB.c.id,
             'isouter': True}
        ],
        'team': [
            {'right': TEAM,
             'onclause': root_select.c.team_id == TEAM.c.id}
        ]
    }


def teams(root_select=models.TEAMS):
    return {
        'topics': [
            {'right': models.JOINS_TOPICS_TEAMS,
             'onclause': models.JOINS_TOPICS_TEAMS.c.team_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.TOPICS,
             'onclause': and_(models.TOPICS.c.id == models.JOINS_TOPICS_TEAMS.c.topic_id,  # noqa
                              models.TOPICS.c.state != 'archived'),
             'isouter': True}],
        'remotecis': [
            {'right': models.REMOTECIS,
             'onclause': and_(models.REMOTECIS.c.team_id == root_select.c.id,
                              models.REMOTECIS.c.state != 'archived'),
             'isouter': True}]
    }


def tests(root_select=models.TESTS):
    return {
        'topics': [
            {'right': models.JOIN_TOPICS_TESTS,
             'onclause': models.JOIN_TOPICS_TESTS.c.test_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.TOPICS,
             'onclause': and_(models.TOPICS.c.id == models.JOIN_TOPICS_TESTS.c.topic_id,  # noqa
                              models.TOPICS.c.state != 'archived'),
             'isouter': True}]
    }


def topics(root_select=models.TOPICS):
    return {
        'teams': [
            {'right': models.JOINS_TOPICS_TEAMS,
             'onclause': models.JOINS_TOPICS_TEAMS.c.topic_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.TEAMS,
             'onclause': and_(models.TEAMS.c.id == models.JOINS_TOPICS_TEAMS.c.team_id,  # noqa
                              models.TEAMS.c.state != 'archived'),
             'isouter': True}]
    }


# associate the name table to the object table
# used for select clause
EMBED_STRING_TO_OBJECT = {
    'jobs': {
        'files': models.FILES,
        'metas': models.METAS,
        'jobdefinition': JOBDEFINITION,
        'jobdefinition.tests': JOBDEFINITION_TESTS,
        'remoteci': REMOTECI,
        'remoteci.tests': REMOTECI_TESTS,
        'components': models.COMPONENTS,
        'team': TEAM},
    'remotecis': {
        'team': TEAM,
        'lastjob': LASTJOB_WITHOUT_CONFIGURATION,
        'lastjob.components': LASTJOB_COMPONENTS,
        'currentjob': CURRENTJOB_WITHOUT_CONFIGURATION,
        'currentjob.components': CURRENTJOB_COMPONENTS},
    'components': {
        'files': CFILES,
        'jobs': JOBS_WITHOUT_CONFIGURATION},
    'files': {
        'jobstate': JOBSTATE,
        'jobstate.job': JOBSTATEJOBS_WITHOUT_CONFIGURATION,
        'job': JOB_WITHOUT_CONFIGURATION,
        'team': TEAM},
    'jobdefinitions': {
        'topic': TOPIC
    },
    'jobstates': {
        'files': models.FILES,
        'job': JOB_WITHOUT_CONFIGURATION,
        'team': TEAM
    },
    'teams': {
        'remotecis': models.REMOTECIS,
        'topics': models.TOPICS
    },
    'tests': {
        'topics': models.TOPICS
    },
    'topics': {
        'teams': models.TEAMS
    }
}


# for each table associate its embed's function handler
EMBED_JOINS = {
    'jobs': jobs,
    'remotecis': remotecis,
    'components': components,
    'files': files,
    'jobdefinitions': jobdefinitions,
    'jobstates': jobstates,
    'teams': teams,
    'tests': tests,
    'topics': topics
}


import collections
Embed = collections.namedtuple('Embed', [
    'many', 'select', 'where', 'sort', 'join'])


def embed(many=False, select=None, where=None,
          sort=None, join=None):
    """Prepare a Embed named tuple

    :param many: True if it's a one-to-many join
    :param select: an optional list of field to embed
    :param where: an extra WHERE clause
    :param sort: an extra ORDER BY clause
    :param join: an SQLAlchemy-core Join instance
    """
    return Embed(many, select, where, sort, join)


def users():
    team = models.TEAMS.alias('team')
    return {
        'team': embed(
            select=[team],
            where=and_(
                team.c.id == models.USERS.c.team_id,
                team.c.state != 'archived'
            ))}
