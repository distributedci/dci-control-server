# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from __future__ import unicode_literals

from dci.api.v1 import performance

from tests import data as tests_data
import tests.utils as t_utils
import collections
import mock

FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


@mock.patch("dci.api.v1.notifications.dispatcher")
def test_compare_performance(user, remoteci_context, team_user_id, topic, topic_user_id):  # noqa
    # create the baseline job
    job_baseline = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    job_baseline = job_baseline.data['job']
    data = {'job_id': job_baseline['id'], 'status': 'success'}
    js_baseline = remoteci_context.post(
        '/api/v1/jobstates',
        data=data).data['jobstate']
    f_1 = t_utils.post_file(user, js_baseline['id'],
                            FileDesc('PBO_Results',
                                     tests_data.jobtest_one),
                            mime='application/junit')
    assert f_1 is not None

    f_11 = t_utils.post_file(user, js_baseline['id'],
                             FileDesc('Tempest',
                                      tests_data.jobtest_one),
                             mime='application/junit')
    assert f_11 is not None

    # create the second job
    job2 = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    job2 = job2.data['job']
    data = {'job_id': job2['id'], 'status': 'success'}
    js_job2 = remoteci_context.post(
        '/api/v1/jobstates',
        data=data).data['jobstate']
    f_2 = t_utils.post_file(user, js_job2['id'],
                            FileDesc('PBO_Results',
                                     tests_data.jobtest_two),
                            mime='application/junit')
    assert f_2 is not None

    f_22 = t_utils.post_file(user, js_job2['id'],
                             FileDesc('Tempest',
                                      tests_data.jobtest_two),
                             mime='application/junit')
    assert f_22 is not None

    res = user.post('/api/v1/performance',
                    headers={'Content-Type': 'application/json'},
                    data={'base_job_id': job_baseline['id'],
                          'jobs': [job2['id']]})

    expected = {'Testsuite_1/test_1': 20.,
                'Testsuite_1/test_2': -25.,
                'Testsuite_1/test_3[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]': 25.}  # noqa

    perf = res.data['performance']
    for tests in perf:
        filename = list(tests.keys())[0]
        for t in tests[filename]:
            if t['job_id'] == job_baseline['id']:
                for tc in t['testscases']:
                    assert tc['delta'] == 0.
            else:
                for tc in t['testscases']:
                    k = '%s/%s' % (tc['classname'], tc['name'])
                    assert expected[k] == tc['delta']


def test_get_performance_tests():
    baseline_test = open('tests/data/perf_test_baseline.xml', 'r')
    test = open('tests/data/perf_test.xml', 'r')

    perf_res = performance.get_performance_tests({'fd': baseline_test,
                                                  'job_id': 'baseline'},
                                                 [{'fd': test,
                                                   'job_id': 'test'}])
    baseline, test = perf_res[0], perf_res[1]
    if perf_res[1]['job_id'] == 'baseline':
        baseline, test = perf_res[1], perf_res[0]

    for tc in baseline['testscases']:
        assert tc['delta'] == 0.0
    assert len(baseline['testscases']) == 3

    expected = {'ci': 930.0, 'rs2': 900.0, 'exit_code': -90.0}
    for tc in test['testscases']:
        assert expected[tc['name']] == tc['delta']
