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

import pytest

import server.tests.utils as utils


class TestAdmin(object):

    def test_post_component_item(self, admin):
        component = utils.create_component(admin)
        assert component.status_code == 201
        assert component.data is not None

    def test_post_test_item(self, admin):
        test = utils.create_test(admin)
        assert test.status_code == 201
        assert test.data is not None

    def test_post_jobdefinition_item(self, admin):
        test = utils.create_test(admin)
        component = utils.create_component(admin)
        jobdefinition = utils.create_jobdefinition(admin, test.data['id'])
        jobdefinition_component = utils.create_jobdefinition_component(
            admin, jobdefinition.data['id'], component.data['id']
        )

        assert jobdefinition_component.status_code == 201
        assert jobdefinition_component.data is not None

    def test_post_remoteci_item(self, admin):
        test = utils.create_test(admin)
        remoteci = utils.create_remoteci(admin, test.data['id'])

        assert remoteci.status_code == 201
        assert remoteci.data is not None

    def test_post_job_item_with_no_testversion_id(self, admin):
        """testversion_id is missing, the server should pick a
        testversion that match the test_id of the remoteci.
        """
        test = utils.create_test(admin)
        utils.create_component(admin)
        utils.create_jobdefinition(admin, test.data['id'])

        remoteci = utils.create_remoteci(admin, test.data['id'])
        job = utils.create_job(admin, remoteci.data['id'])

        assert job.status_code == 201
        assert job.data is not None

    def test_get_job_item(self, admin, company_a_user):
        """GET /jobs should retrieve the item and feed the
        data key with the data section from the component, remoteci,
        test and version.
        """
        test = utils.create_test(admin)
        component = utils.create_component(admin)
        jobdefinition = utils.create_jobdefinition(admin, test.data['id'])

        utils.create_jobdefinition_component(
            admin, jobdefinition.data['id'], component.data['id']
        )
        remoteci = utils.create_remoteci(admin, test.data['id'])

        job = utils.create_job(admin, remoteci.data['id'])
        job = company_a_user.get('/api/jobs/%s' % job.data['id'])

        assert job.status_code == 200
        assert job.data['data'] == {
            'component_keys': {'foo': ['bar1', 'bar2']},
            'remoteci_keys': {'foo': ['bar1', 'bar2']},
            'test_keys': {'foo': ['bar1', 'bar2']}
        }

    def test_job_recheck(self, admin):
        test = utils.create_test(admin)
        component = utils.create_component(admin)
        jobdefinition = utils.create_jobdefinition(admin, test.data['id'])

        utils.create_jobdefinition_component(
            admin, jobdefinition.data['id'], component.data['id']
        )
        remoteci = utils.create_remoteci(admin, test.data['id'])
        remoteci_id = remoteci.data['id']

        job_to_recheck = utils.create_job(admin, remoteci_id)
        job_to_recheck_id = job_to_recheck.data['id']

        recheck_job = utils.create_job(admin, remoteci_id, True,
                                       job_to_recheck_id)
        recheck_job_id = recheck_job.data['id']

        job_to_recheck = admin.get('/api/jobs/%s' % job_to_recheck_id)
        recheck_job = admin.get('/api/jobs/%s' % recheck_job_id)

        assert recheck_job.status_code == 200
        assert (recheck_job.data['remoteci'] ==
                job_to_recheck.data['remoteci'])
        assert (recheck_job.data['jobdefinition'] ==
                job_to_recheck.data['jobdefinition'])
        assert recheck_job.data['team_id'] == job_to_recheck.data['team_id']
        assert recheck_job.data['recheck'] is True

    @pytest.mark.parametrize(('status'), ['new', 'initializing', 'ongoing'])
    def test_get_job_should_kill_existing_jobs(
            self, admin, company_a_user, status):
        """GET /jobs should retrieve a new job and kill the existing ones.
        """
        test = utils.create_test(admin)
        remoteci = utils.create_remoteci(admin, test.data['id'])

        def get_job_status(job_id):
            r = company_a_user.get(
                '/api/jobs/%s?embedded={"jobstates": 1}' % job_id)
            return r.data['jobstates'][0]['status']

        utils.create_jobdefinition(admin, test.data['id'], name=('test_1'))
        utils.create_jobdefinition(admin, test.data['id'], name=('test_2'))

        first_job = utils.create_job(company_a_user, remoteci.data['id'])
        utils.create_jobstate(
            company_a_user, first_job.data['id'], status=status)
        assert get_job_status(first_job.data['id']) == status

        # create another job for the remoteci, the previous job won't finish
        # and so, should get the 'unfinished' status.
        utils.create_job(company_a_user, remoteci.data['id'])
        assert get_job_status(first_job.data['id']) == 'unfinished'
