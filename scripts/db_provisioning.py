#!/usr/bin/env python
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

import collections
import datetime
import dci.auth as auth
import dci.db.models as models
import functools
import getopt
import six.moves
import sqlalchemy
import sqlalchemy_utils.functions
import sys

from dci import dci_config

conf = dci_config.generate_conf()


def time_helper():
    dt = datetime.datetime
    td = datetime.timedelta

    time = collections.defaultdict(dict)

    for day in range(4):
        for hour in range(24):
            time[day][hour] = dt.now() - td(days=day, hours=hour)

    return time


def write(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)

JUNIT_TEMPEST = open('tests/data/tempest-results.xml', 'r').read()
JUNIT_RALLY = open('tests/data/rally-results.xml', 'r').read()
STACK_DETAILS = open('scripts/data/tripleo-stack-dump-sample.json', 'r').read()


def db_insert(db_conn, model_item, **kwargs):
    query = model_item.insert().values(**kwargs)
    return db_conn.execute(query).inserted_primary_key[0]


def init_db(db_conn, minimal, file):
    """Initialize the database with fake datas

    Create an admin team and 2 other teams HP and DELL
    Create 3 topics, 1 common and 2 scoped, 1 for each team
    """

    db_ins = functools.partial(db_insert, db_conn)
    time = time_helper()

    # Create a super admin
    team_admin = db_ins(models.TEAMS, name='admin')

    # Create the three mandatory roles
    super_admin_role = {
        'name': 'Super Admin',
        'label': 'SUPER_ADMIN',
        'description': 'Admin of the platform',
    }

    admin_role = {
        'name': 'Admin',
        'label': 'ADMIN',
        'description': 'Admin of a team',
    }

    user_role = {
        'name': 'User',
        'label': 'USER',
        'description': 'Regular User',
    }

    admin_role_id = db_ins(models.ROLES, **admin_role)
    user_role_id = db_ins(models.ROLES, **user_role)
    super_admin_role_id = db_ins(models.ROLES, **super_admin_role)

    db_ins(models.USERS, name='admin', role='admin',
           role_id=super_admin_role_id, team_id=team_admin,
           password=auth.hash_password('admin'))

    if minimal:
        return

    # Create two other teams
    team_hp = db_ins(models.TEAMS, name='hp')
    team_dell = db_ins(models.TEAMS, name='dell')

    # Creates according users, 1 admin 1 user for other teams
    db_ins(models.USERS, name='user_hp', role='user',
           role_id=user_role_id, team_id=team_hp,
           password=auth.hash_password('password'))

    db_ins(models.USERS, name='admin_hp', role='admin',
           role_id=admin_role_id, team_id=team_hp,
           password=auth.hash_password('password'))

    db_ins(models.USERS, name='user_dell', role='user',
           role_id=user_role_id, team_id=team_dell,
           password=auth.hash_password('password'))

    db_ins(models.USERS, name='admin_dell', role='admin',
           role_id=admin_role_id, team_id=team_dell,
           password=auth.hash_password('password'))

    # Create 3 topics, 1 common and 2 scoped
    topic_common = db_ins(models.TOPICS, name='topic_common')

    topic_hp = db_ins(models.TOPICS, name='topic_HP')
    topic_dell = db_ins(models.TOPICS, name='topic_DELL')

    # Attach teams to topics
    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_common,
           team_id=team_admin)
    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_hp,
           team_id=team_admin)
    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_dell,
           team_id=team_admin)

    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_common, team_id=team_hp)
    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_hp, team_id=team_hp)

    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_common, team_id=team_dell)
    db_ins(models.JOINS_TOPICS_TEAMS, topic_id=topic_dell, team_id=team_dell)

    # Create 2 remotecis per team
    remoteci_hp_1 = {
        'name': 'HP_1', 'team_id': team_hp,
        'data': {
            'storage': 'netapp', 'network': 'HP', 'hardware': 'Intel',
            'virtualization': 'KVM'
        }
    }
    remoteci_hp_1 = db_ins(models.REMOTECIS, **remoteci_hp_1)

    remoteci_hp_2 = {
        'name': 'HP_2', 'team_id': team_hp,
        'data': {
            'storage': 'ceph', 'network': 'Cisco', 'hardware': 'HP',
            'virtualization': 'VMWare'
        }
    }
    remoteci_hp_2 = db_ins(models.REMOTECIS, **remoteci_hp_2)

    remoteci_dell_1 = {
        'name': 'Dell_1', 'team_id': team_dell,
        'data': {
            'storage': 'swift', 'network': 'Juniper', 'hardware': 'Dell',
            'virtualization': 'Xen'
        }
    }
    remoteci_dell_1 = db_ins(models.REMOTECIS, **remoteci_dell_1)

    remoteci_dell_2 = {
        'name': 'Dell_2', 'team_id': team_dell,
        'data': {
            'storage': 'AWS', 'network': 'Brocade', 'hardware': 'Huawei',
            'virtualization': 'HyperV'
        }
    }
    remoteci_dell_2 = db_ins(models.REMOTECIS, **remoteci_dell_2)

    # Create 2 components per topic
    component_common_1 = db_ins(
        models.COMPONENTS, topic_id=topic_common, type='git', name='Khaleesi',
        created_at=time[3][15]
    )
    component_common_2 = db_ins(
        models.COMPONENTS, topic_id=topic_common, type='image',
        name='RDO Manager', created_at=time[2][20]
    )
    component_hp_1 = db_ins(
        models.COMPONENTS, topic_id=topic_hp, type='package',
        name='OSP director', created_at=time[3][5]
    )
    component_hp_2 = db_ins(
        models.COMPONENTS, topic_id=topic_hp, type='gerrit_review',
        name='DCI-control-server', created_at=time[2][2]
    )

    component_dell_1 = db_ins(
        models.COMPONENTS, topic_id=topic_dell, type='git', name='Khaleesi',
        created_at=time[2][21]
    )
    component_dell_2 = db_ins(
        models.COMPONENTS, topic_id=topic_dell,
        type='package', name='OSP director', created_at=time[3][12]
    )

    # Create 2 jobdefinitions per topic
    jobdef_common_1 = db_ins(models.JOBDEFINITIONS, topic_id=topic_common,
                             name='Common tox v0.8', component_types=['git'])
    jobdef_common_2 = db_ins(models.JOBDEFINITIONS, topic_id=topic_common,
                             name='Common tox v2.1.1', component_types=['git'])

    jobdef_hp_1 = db_ins(models.JOBDEFINITIONS, topic_id=topic_hp,
                         name='HP tempest v0.4.2',
                         component_types=['OSP director'])
    jobdef_hp_2 = db_ins(models.JOBDEFINITIONS, topic_id=topic_hp,
                         name='HP tempest v1.1',
                         component_types=['package', 'gerrit_review'])

    jobdef_dell_1 = db_ins(models.JOBDEFINITIONS, topic_id=topic_dell,
                           name='Dell khaleesi-tempest v0.8',
                           component_types=['git'])
    jobdef_dell_2 = db_ins(models.JOBDEFINITIONS, topic_id=topic_dell,
                           name='Dell khaleesi-tempest v1.2.15',
                           component_types=['git', 'package'])

    # Creates 3 tests type
    test_common = db_ins(models.TESTS, name='tox', team_id=team_admin)
    test_hp = db_ins(models.TESTS, name='tempest', team_id=team_hp)
    test_dell = db_ins(models.TESTS, name='khaleesi-tempest',
                       team_id=team_dell)

    db_ins(models.JOIN_JOBDEFINITIONS_TESTS, jobdefinition_id=jobdef_common_1,
           test_id=test_common)
    db_ins(models.JOIN_JOBDEFINITIONS_TESTS, jobdefinition_id=jobdef_common_2,
           test_id=test_common)
    db_ins(models.JOIN_JOBDEFINITIONS_TESTS, jobdefinition_id=jobdef_hp_1,
           test_id=test_hp)
    db_ins(models.JOIN_JOBDEFINITIONS_TESTS, jobdefinition_id=jobdef_hp_2,
           test_id=test_hp)
    db_ins(models.JOIN_JOBDEFINITIONS_TESTS, jobdefinition_id=jobdef_dell_1,
           test_id=test_dell)
    db_ins(models.JOIN_JOBDEFINITIONS_TESTS, jobdefinition_id=jobdef_dell_2,
           test_id=test_dell)

    # Creates 4 jobs for each jobdefinition (4*6=24 in total for pagination)
    job_id = db_ins(
        models.JOBS, status='new', jobdefinition_id=jobdef_common_1,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[0][1],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_1
    )
    job_id = db_ins(
        models.JOBS, status='new', jobdefinition_id=jobdef_common_1,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[0][2],
        updated_at=time[0][2], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_1
    )
    job_id = db_ins(
        models.JOBS, status='pre-run', jobdefinition_id=jobdef_common_1,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[0][2],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_1
    )
    job_id = db_ins(
        models.JOBS, status='pre-run', jobdefinition_id=jobdef_common_2,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[0][3],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_2
    )
    job_id = db_ins(
        models.JOBS, status='running', jobdefinition_id=jobdef_common_2,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[0][10],
        updated_at=time[0][3], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_2
    )
    job_id = db_ins(
        models.JOBS, status='running', jobdefinition_id=jobdef_common_2,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[0][14],
        updated_at=time[0][7], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_2
    )
    job_id = db_ins(
        models.JOBS, status='post-run', jobdefinition_id=jobdef_hp_1,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[1][0],
        updated_at=time[0][10], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_1
    )
    job_id = db_ins(
        models.JOBS, status='post-run', jobdefinition_id=jobdef_hp_1,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[0][20],
        updated_at=time[0][2], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_1
    )
    job_id = db_ins(
        models.JOBS, status='failure', jobdefinition_id=jobdef_hp_1,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[2][10],
        updated_at=time[1][3], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_1
    )
    job_id = db_ins(
        models.JOBS, status='failure', jobdefinition_id=jobdef_hp_2,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[1][1],
        updated_at=time[0][0], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_2
    )
    job_id = db_ins(
        models.JOBS, status='success', jobdefinition_id=jobdef_hp_2,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[3][12],
        updated_at=time[2][20], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_2
    )
    job_id = db_ins(
        models.JOBS, status='success', jobdefinition_id=jobdef_hp_2,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[3][20],
        updated_at=time[0][6], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_2
    )
    job_id = db_ins(
        models.JOBS, status='killed', jobdefinition_id=jobdef_hp_2,
        remoteci_id=remoteci_hp_1, team_id=team_hp, created_at=time[1][8],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_2
    )
    job_id = db_ins(
        models.JOBS, status='killed', jobdefinition_id=jobdef_hp_2,
        remoteci_id=remoteci_hp_2, team_id=team_hp, created_at=time[2][12],
        updated_at=time[1][6], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_hp_2
    )
    job_id = db_ins(
        models.JOBS, status='new', jobdefinition_id=jobdef_common_1,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[0][1],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_1
    )
    job_id = db_ins(
        models.JOBS, status='new', jobdefinition_id=jobdef_common_1,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[0][2],
        updated_at=time[0][2], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_1
    )
    job_id = db_ins(
        models.JOBS, status='pre-run', jobdefinition_id=jobdef_common_1,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[0][2],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_1
    )
    job_id = db_ins(
        models.JOBS, status='pre-run', jobdefinition_id=jobdef_common_2,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[0][3],
        updated_at=time[0][1], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_2
    )
    job_id = db_ins(
        models.JOBS, status='running', jobdefinition_id=jobdef_common_2,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[0][10],
        updated_at=time[0][3], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_2
    )
    job_id = db_ins(
        models.JOBS, status='running', jobdefinition_id=jobdef_common_2,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[0][14],
        updated_at=time[0][7], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_common_2
    )
    job_id = db_ins(
        models.JOBS, status='post-run', jobdefinition_id=jobdef_dell_1,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[1][0],
        updated_at=time[0][10], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_dell_1
    )
    job_id = db_ins(
        models.JOBS, status='post-run', jobdefinition_id=jobdef_dell_1,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[0][20],
        updated_at=time[0][2], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_dell_1
    )
    job_dell_9 = db_ins(
        models.JOBS, status='failure', jobdefinition_id=jobdef_dell_1,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[2][10],
        updated_at=time[1][3], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_dell_9,
        component_id=component_dell_1
    )
    job_dell_10 = db_ins(
        models.JOBS, status='failure', jobdefinition_id=jobdef_dell_2,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[1][1],
        updated_at=time[0][0], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_dell_10,
        component_id=component_dell_2
    )
    job_dell_11 = db_ins(
        models.JOBS, status='success', jobdefinition_id=jobdef_dell_2,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[3][12],
        updated_at=time[2][20], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_dell_11,
        component_id=component_dell_2
    )
    job_dell_12 = db_ins(
        models.JOBS, status='success', jobdefinition_id=jobdef_dell_2,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[3][20],
        updated_at=time[0][0], configuration=STACK_DETAILS,
        user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_dell_12,
        component_id=component_dell_2
    )
    job_id = db_ins(
        models.JOBS, status='killed', jobdefinition_id=jobdef_dell_2,
        remoteci_id=remoteci_dell_1, team_id=team_dell, created_at=time[1][4],
        updated_at=time[0][3], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_dell_2
    )
    job_id = db_ins(
        models.JOBS, status='killed', jobdefinition_id=jobdef_dell_2,
        remoteci_id=remoteci_dell_2, team_id=team_dell, created_at=time[2][8],
        updated_at=time[1][2], user_agent='python-dciclient_0.1.0'
    )
    db_ins(
        models.JOIN_JOBS_COMPONENTS, job_id=job_id,
        component_id=component_dell_2
    )

    # Creates jobstates attached to jobs, just create a subset of them to
    # avoid explosion of complexity

    # DELL Job 9
    db_ins(
        models.JOBSTATES, status='new', team_id=team_dell,
        created_at=time[2][10], job_id=job_dell_9
    )
    db_ins(
        models.JOBSTATES, status='pre-run', team_id=team_dell,
        created_at=time[2][1], job_id=job_dell_9
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[2][0], job_id=job_dell_9
    )
    db_ins(
        models.JOBSTATES, status='post-run', team_id=team_dell,
        created_at=time[1][5], job_id=job_dell_9
    )
    db_ins(
        models.JOBSTATES, status='failure', team_id=team_dell,
        created_at=time[1][3], job_id=job_dell_9
    )

    # DELL Job 10
    db_ins(
        models.JOBSTATES, status='new', team_id=team_dell,
        created_at=time[1][1], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='pre-run', team_id=team_dell,
        created_at=time[1][0], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[0][23], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[0][15], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[0][11], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='post-run', team_id=team_dell,
        created_at=time[0][2], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='post-run', team_id=team_dell,
        created_at=time[0][1], job_id=job_dell_10
    )
    db_ins(
        models.JOBSTATES, status='failure', team_id=team_dell,
        created_at=time[0][0], job_id=job_dell_10
    )

    # Dell Job 11
    db_ins(
        models.JOBSTATES, status='new', team_id=team_dell,
        created_at=time[3][12], job_id=job_dell_11
    )
    db_ins(
        models.JOBSTATES, status='pre-run', team_id=team_dell,
        created_at=time[3][11], job_id=job_dell_11
    )
    db_ins(
        models.JOBSTATES, status='pre-run', team_id=team_dell,
        created_at=time[3][10], job_id=job_dell_11
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[3][1], job_id=job_dell_11
    )
    db_ins(
        models.JOBSTATES, status='post-run', team_id=team_dell,
        created_at=time[2][22], job_id=job_dell_11
    )
    db_ins(
        models.JOBSTATES, status='success', team_id=team_dell,
        created_at=time[2][20], job_id=job_dell_11
    )

    # DELL Job 12
    db_ins(
        models.JOBSTATES, status='new', team_id=team_dell,
        created_at=time[3][20], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='pre-run', team_id=team_dell,
        created_at=time[3][15], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[3][14], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[3][2], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[2][18], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[1][5], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[1][0], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[0][22], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='running', team_id=team_dell,
        created_at=time[0][13], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='post-run', team_id=team_dell,
        created_at=time[0][12], job_id=job_dell_12
    )
    db_ins(
        models.JOBSTATES, status='post-run', team_id=team_dell,
        created_at=time[0][10], job_id=job_dell_12
    )
    job_dell_12_12 = db_ins(
        models.JOBSTATES, status='success', team_id=team_dell,
        created_at=time[0][0], job_id=job_dell_12
    )

    # create files only for the last job i.e: dell_12
    f_id = db_ins(
        models.FILES, name='', mime='application/junit',
        created_at=time[0][0], team_id=team_dell, job_id=job_dell_12
    )

    swift = dci_config.get_store('files')

    if file:
        file_path = swift.build_file_path(team_dell, job_dell_12, f_id)
        swift.upload(file_path, JUNIT_TEMPEST)

    f_id2 = db_ins(
        models.FILES, name='Rally test suite', mime='application/junit',
        created_at=time[0][0], team_id=team_dell, job_id=job_dell_12
    )

    if file:
        file_path = swift.build_file_path(team_dell, job_dell_12, f_id2)
        swift.upload(file_path, JUNIT_RALLY)

    f_id = db_ins(
        models.FILES, name='foo.txt', mime='text/play',
        created_at=time[0][0], team_id=team_dell, jobstate_id=job_dell_12_12
    )

    if file:
        file_path = swift.build_file_path(team_dell, job_dell_12, f_id)
        swift.upload(file_path, 'some content')

    f_id = db_ins(
        models.FILES, name='bar.txt', mime='text/play',
        created_at=time[0][0], team_id=team_dell, jobstate_id=job_dell_12_12
    )

    if file:
        file_path = swift.build_file_path(team_dell, job_dell_12, f_id)
        swift.upload(file_path, 'some other content')


if __name__ == '__main__':
    db_uri = conf['SQLALCHEMY_DATABASE_URI']
    minimal, force, file = False, False, False

    opts, _ = getopt.getopt(sys.argv[1:], 'ymf')
    for opt in opts:
        if opt == ('-y', ''):
            force = True
        if opt == ('-m', ''):
            minimal = True
        if opt == ('-f', ''):
            file = True

    if not force:
        print('you can force the deletion by adding -y as a parameter')

    if sqlalchemy_utils.functions.database_exists(db_uri):
        while not force:
            print('Be carefull this script will override your database:')
            print(db_uri)
            print('')
            i = six.moves.input('Continue ? [y/N] ').lower()
            if not i or i == 'n':
                sys.exit(0)
            if i == 'y':
                break

        sqlalchemy_utils.functions.drop_database(db_uri)

    sqlalchemy_utils.functions.create_database(db_uri)

    engine = sqlalchemy.create_engine(db_uri)
    models.metadata.create_all(engine)
    with engine.begin() as conn:
        init_db(conn, minimal, file)
