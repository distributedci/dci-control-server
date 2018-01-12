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

from __future__ import unicode_literals
import mock
import pytest
import six
import uuid

from dci.stores.swift import Swift
from dci.common import utils
from tests.data import JUNIT

SWIFT = 'dci.stores.swift.Swift'


def test_create_jobs(remoteci_context, components_user_ids):
    data = {'comment': 'kikoolol', 'components': components_user_ids}
    job = remoteci_context.post('/api/v1/jobs', data=data)
    job_id = job.data['job']['id']

    assert job.status_code == 201
    assert job.data['job']['comment'] == 'kikoolol'

    job = remoteci_context.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200
    assert job.data['job']['comment'] == 'kikoolol'


def test_create_jobs_empty_comment(remoteci_context, components_user_ids):
    data = {'components': components_user_ids}
    job = remoteci_context.post('/api/v1/jobs', data=data).data
    assert job['job']['comment'] is None

    job = remoteci_context.get('/api/v1/jobs/%s' % job['job']['id']).data
    assert job['job']['comment'] is None


def test_get_all_jobs(user, remoteci_context, topic_user_id,
                      components_user_ids):
    data = {'components_ids': components_user_ids,
            'topic_id': topic_user_id}
    job_1 = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    job_1_id = job_1.data['job']['id']

    job_2 = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    job_2_id = job_2.data['job']['id']

    db_all_jobs = user.get('/api/v1/jobs?sort=created_at').data
    db_all_jobs = db_all_jobs['jobs']
    db_all_jobs_ids = [db_job['id'] for db_job in db_all_jobs]

    assert db_all_jobs_ids == [job_1_id, job_2_id]


def test_get_all_jobs_with_pagination(remoteci_context,
                                      components_user_ids, test_id):
    data = {'components': components_user_ids}
    remoteci_context.post('/api/v1/jobs', data=data)
    remoteci_context.post('/api/v1/jobs', data=data)
    remoteci_context.post('/api/v1/jobs', data=data)
    remoteci_context.post('/api/v1/jobs', data=data)

    jobs = remoteci_context.get('/api/v1/jobs').data
    assert jobs['_meta']['count'] == 4

    # verify limit and offset are working well
    jobs = remoteci_context.get('/api/v1/jobs?limit=2&offset=0').data
    assert len(jobs['jobs']) == 2

    jobs = remoteci_context.get('/api/v1/jobs?limit=2&offset=2').data
    assert len(jobs['jobs']) == 2

    # if offset is out of bound, the api returns an empty list
    jobs = remoteci_context.get('/api/v1/jobs?limit=5&offset=300')
    assert jobs.status_code == 200
    assert jobs.data['jobs'] == []


def test_get_all_jobs_with_embed(admin, remoteci_context, team_user_id,
                                 remoteci_user_id, components_user_ids):
    # create 2 jobs and check meta data count
    data = {'components': components_user_ids}
    job_1 = remoteci_context.post('/api/v1/jobs', data=data)
    job_2 = remoteci_context.post('/api/v1/jobs', data=data)

    # Create two ISSUES
    data = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/1'
    }
    issue_1 = admin.post('/api/v1/jobs/%s/issues' % job_1.data['job']['id'],
                         data=data).data
    data = {
        'url': 'https://github.com/redhat-cip/dci-control-server/issues/2'
    }
    issue_2 = admin.post('/api/v1/jobs/%s/issues' % job_2.data['job']['id'],
                         data=data).data

    # verify embed with all embedded options
    query_embed = ('/api/v1/jobs?embed='
                   'team,remoteci,jobstates,issues,rconfiguration')
    jobs = admin.get(query_embed).data

    for job in jobs['jobs']:
        assert 'team' in job
        assert job['team']['id'] == team_user_id
        assert job['team_id'] == job['team']['id']
        assert 'remoteci' in job
        assert 'issues' in job
        assert job['remoteci']['id'] == remoteci_user_id
        assert job['remoteci_id'] == job['remoteci']['id']
        assert job['rconfiguration'] == {}

    assert jobs['jobs'][1]['issues'][0]['id'] == issue_1['issue']['id']
    assert jobs['jobs'][0]['issues'][0]['id'] == issue_2['issue']['id']

    query_embed = ('/api/v1/jobs?embed=components')
    jobs = admin.get(query_embed).data
    assert jobs['_meta']['count'] == 2
    assert len(jobs['jobs']) == 2
    for job in jobs['jobs']:
        cur_set = set(i['id'] for i in job['components'])
        assert cur_set == set(components_user_ids)

    with mock.patch(SWIFT, spec=Swift) as mock_swift:
            mockito = mock.MagicMock()
            head_result = {
                'etag': utils.gen_etag(),
                'content-type': "stream",
                'content-length': 7
            }

            def get(a):
                return True, six.StringIO(JUNIT),

            mockito.head.return_value = head_result
            mockito.get = get
            mock_swift.return_value = mockito
            query = ('/api/v1/jobs')
            jobs = admin.get(query).data
            for job in jobs['jobs']:
                headers = {'DCI-JOB-ID': job['id'],
                           'DCI-NAME': 'name1',
                           'DCI-MIME': 'application/junit'}
                admin.post('/api/v1/files', headers=headers, data=JUNIT)
    jobs = admin.get('/api/v1/jobs?embed=results').data
    assert jobs['_meta']['count'] == 2
    assert len(jobs['jobs']) == 2
    for job in jobs['jobs']:
        assert len(job['results']) == 1


def test_get_all_jobs_with_duplicated_embed(admin, team_user_id,
                                            remoteci_context,
                                            remoteci_user_id,
                                            components_user_ids,
                                            topic_user_id):
    test_jd = admin.post('/api/v1/tests',
                         data={'name': 'test_topic',
                               'team_id': team_user_id}).data
    test_jd_id = test_jd['test']['id']
    test_rci = admin.post('/api/v1/tests',
                          data={'name': 'test_remoteci',
                                'team_id': team_user_id}).data
    test_rci_id = test_rci['test']['id']
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test_jd_id})
    admin.post('/api/v1/remotecis/%s/tests' % remoteci_user_id,
               data={'test_id': test_rci_id})

    data = {'topic_id': topic_user_id,
            'components': components_user_ids}

    remoteci_context.post('/api/v1/jobs', data=data)
    query_embed = (('/api/v1/jobs?embed='
                    'metas,topic,topic.tests,components,'
                    'files,topic,team,remoteci,remoteci.tests'))
    jobs = remoteci_context.get(query_embed).data
    assert len(jobs['jobs']) == 1
    assert len(jobs['jobs'][0]['components']) == 3
    assert len(jobs['jobs'][0]['topic']['tests']) == 1
    assert jobs['jobs'][0]['topic']['tests'][0]['id'] == test_jd_id
    assert jobs['jobs'][0]['remoteci']['tests'][0]['id'] == test_rci_id


def test_get_all_jobs_with_embed_and_limit(remoteci_context,
                                           components_user_ids):
    # create 2 jobs and check meta data count
    data = {'components': components_user_ids}
    remoteci_context.post('/api/v1/jobs', data=data)
    remoteci_context.post('/api/v1/jobs', data=data)

    # verify embed with all embedded options
    query_embed = ('/api/v1/jobs?embed=components&limit=1')
    jobs = remoteci_context.get(query_embed).data

    assert len(jobs['jobs']) == 1
    assert len(jobs['jobs'][0]['components']) == 3


def test_get_all_jobs_with_embed_not_valid(remoteci_context):
    jds = remoteci_context.get('/api/v1/jobs?embed=mdr')
    assert jds.status_code == 400


def test_update_job(admin, remoteci_context, components_user_ids):
    data = {
        'comment': 'foo',
        'components': components_user_ids
    }
    job = remoteci_context.post('/api/v1/jobs', data=data)
    job = job.data['job']

    assert job['comment'] == 'foo'

    data_update = {'status': 'failure', 'comment': 'bar'}

    res = admin.put('/api/v1/jobs/%s' % job['id'], data=data_update,
                    headers={'If-match': job['etag']})

    assert res.status_code == 204

    res = remoteci_context.get('/api/v1/jobs/%s' % job['id'])
    job = res.data['job']

    assert res.status_code == 200
    assert job['status'] == 'failure'
    assert job['comment'] == 'bar'


def test_success_update_job_status(admin, job_user_id):
    job = admin.get('/api/v1/jobs/%s' % job_user_id)
    job = job.data['job']

    assert job['status'] == 'new'

    data_update = {'status': 'pre-run'}
    job = admin.put('/api/v1/jobs/%s' % job_user_id, data=data_update,
                    headers={'If-match': job['etag']})
    job = admin.get('/api/v1/jobs/%s' % job_user_id).data['job']

    assert job['status'] == 'pre-run'

    data_update = {'status': 'failure'}
    job = admin.put('/api/v1/jobs/%s' % job_user_id, data=data_update,
                    headers={'If-match': job['etag']})
    job = admin.get('/api/v1/jobs/%s' % job_user_id).data['job']

    assert job['status'] == 'failure'


def test_job_notification(app, user, remoteci_user_id, user_id, job_user_id):

    with app.app_context():
        data = {'user_id': user_id}
        user.post('/api/v1/remotecis/%s/users' % remoteci_user_id,
                  data=data)

        job = user.get('/api/v1/jobs/%s' % job_user_id)
        job = job.data['job']

        data_post = {'mesg': 'test'}

        with mock.patch('dci.api.v1.jobs.flask.g.sender.send_json') as f_s:
            res = user.post('/api/v1/jobs/%s/notify' % job_user_id,
                            data=data_post)
            assert res.status_code == 204
            f_s.assert_called_once_with(
                {'event': 'notification',
                 'emails': ['user@example.org'],
                 'job_id': job_user_id,
                 'remoteci_id': remoteci_user_id,
                 'topic_id': job['topic_id'],
                 'status': 'new',
                 'mesg': 'test'})


def test_get_all_jobs_with_where(admin, team_user_id, job_user_id):
    db_job = admin.get('/api/v1/jobs?where=id:%s' % job_user_id).data
    db_job_id = db_job['jobs'][0]['id']
    assert db_job_id == job_user_id

    db_job = admin.get(
        '/api/v1/jobs?where=team_id:%s' % team_user_id).data
    db_job_id = db_job['jobs'][0]['id']
    print(db_job)
    assert db_job_id == job_user_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/jobs?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_jobs_with_sort(remoteci_context, components_user_ids):
    # create 3 jobs ordered by created time
    data = {'components': components_user_ids}
    job_1 = remoteci_context.post('/api/v1/jobs', data=data).data['job']
    job_2 = remoteci_context.post('/api/v1/jobs', data=data).data['job']
    job_3 = remoteci_context.post('/api/v1/jobs', data=data).data['job']

    jobs = remoteci_context.get('/api/v1/jobs?sort=created_at').data
    assert jobs['jobs'] == [job_1, job_2, job_3]

    # reverse order by created_at
    jobs = remoteci_context.get('/api/v1/jobs?sort=-created_at').data
    assert jobs['jobs'] == [job_3, job_2, job_1]


def test_get_job_by_id(remoteci_context, components_user_ids):
    job = remoteci_context.post('/api/v1/jobs',
                                data={'components': components_user_ids})
    job_id = job.data['job']['id']

    job = remoteci_context.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200

    job = job.data
    assert job['job']['id'] == job_id


def test_get_jobstates_by_job_id(admin, job_user_id):
    data = {'status': 'new', 'job_id': job_user_id}
    jobstate_ids = set([
        admin.post('/api/v1/jobstates', data=data).data['jobstate']['id'],
        admin.post('/api/v1/jobstates', data=data).data['jobstate']['id']])

    jobstates = admin.get('/api/v1/jobs/%s/jobstates' % job_user_id)
    jobstates = jobstates.data['jobstates']

    found_jobstate_ids = set(i['id'] for i in jobstates)
    assert jobstate_ids == found_jobstate_ids

    # verify embed with all embedded options
    jobstates = admin.get('/api/v1/jobs/%s?embed=jobstates' % job_user_id)
    assert len(jobstates.data['job']['jobstates']) == len(found_jobstate_ids)


def test_get_jobstates_by_job_id_with_embed(admin, job_user_id, jobstate_user_id):  # noqa
    with mock.patch(SWIFT, spec=Swift) as mock_swift:
        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
                   'DCI-NAME': 'name1'}
        pfile = admin.post('/api/v1/files',
                           headers=headers,
                           data='kikoolol').data
        file1_id = pfile['file']['id']
        headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
                   'DCI-NAME': 'name2'}
        pfile = admin.post('/api/v1/files',
                           headers=headers,
                           data='kikoolol').data
        file2_id = pfile['file']['id']
        jobstates = admin.get('/api/v1/jobs/%s/jobstates'
                              '?embed=files&sort=files.name' % job_user_id)  # noqa
        jobstate = jobstates.data['jobstates'][0]
        assert jobstate['files'][0]['id'] == file1_id
        assert jobstate['files'][1]['id'] == file2_id

        jobstates = admin.get('/api/v1/jobs/%s/jobstates'
                              '?embed=files&sort=-files.name' % job_user_id)  # noqa
        jobstate = jobstates.data['jobstates'][0]
        assert jobstate['files'][0]['id'] == file2_id
        assert jobstate['files'][1]['id'] == file1_id


def test_embed_with_subkey_in_where(admin, job_user_id):
    jobstates = admin.get('/api/v1/jobs?embed=team&'
                          'where=team.state:inactive')
    assert jobstates.data['_meta']['count'] == 0
    jobstates = admin.get('/api/v1/jobs?embed=team&'
                          'where=team.state:active')
    assert jobstates.data['_meta']['count'] > 0

    # ensure we get the valid_keys list of the subtable in the
    # error message
    jobstates = admin.get('/api/v1/jobs?embed=team&'
                          'where=team.invalid_key:active')
    assert jobstates.status_code == 400
    valid_subkeys = jobstates.data['payload']['valid_keys']
    jobstates = admin.get('/api/v1/jobs?embed=team&'
                          'where=invalid_key.team:active')
    assert jobstates.status_code == 400
    valid_keys = jobstates.data['payload']['valid_keys']
    assert set(valid_keys) != set(valid_subkeys)


def test_get_job_not_found(admin):
    result = admin.get('/api/v1/jobs/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobs_with_schedule(remoteci_context, topic_user_id,
                                components_user_ids):
    # schedule a job
    data = {'topic_id': topic_user_id}
    job = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert job.status_code == 201
    job_id = job.data['job']['id']

    # get the components of the scheduled jobs
    job_components = remoteci_context.get(
        '/api/v1/jobs/%s/components' % job_id
    ).data
    for c in job_components['components']:
        url = '/api/v1/components/%s?embed=jobs' % c['id']
        component = remoteci_context.get(url).data
        assert component['component']['jobs'][0]['id'] == job_id


def test_delete_job_by_id(remoteci_context, components_user_ids):

    job = remoteci_context.post('/api/v1/jobs',
                                data={'components': components_user_ids})
    job_id = job.data['job']['id']
    job_etag = job.headers.get("ETag")
    assert job.status_code == 201

    job = remoteci_context.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200

    deleted_job = remoteci_context.delete('/api/v1/jobs/%s' % job_id,
                                          headers={'If-match': job_etag})
    assert deleted_job.status_code == 204

    job = remoteci_context.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 404


def test_delete_job_archive_dependencies(admin, job_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito

        headers = {'DCI-JOB-ID': job_user_id, 'DCI-NAME': 'afile.txt',
                   'Content-Type': 'text/plain'}

        file = admin.post('/api/v1/files', headers=headers, data='content')
        assert file.status_code == 201

        url = '/api/v1/jobs/%s' % job_user_id
        job = admin.get(url)
        etag = job.data['job']['etag']
        assert job.status_code == 200

        deleted_job = admin.delete(url, headers={'If-match': etag})
        assert deleted_job.status_code == 204

        url = '/api/v1/files/%s' % file.data['file']['id']
        file = admin.get(url)
        assert file.status_code == 404


# Tests for the isolation


def test_get_all_jobs_as_user(user, team_user_id, job_user_id):
    jobs = user.get('/api/v1/jobs')
    assert jobs.status_code == 200
    assert jobs.data['_meta']['count'] == 1
    for job in jobs.data['jobs']:
        assert job['team_id'] == team_user_id


def test_get_all_jobs_as_product_owner(product_owner, team_user_id,
                                       job_user_id):
    jobs = product_owner.get('/api/v1/jobs')
    assert jobs.status_code == 200
    assert jobs.data['_meta']['count'] == 1
    for job in jobs.data['jobs']:
        assert job['team_id'] == team_user_id


def test_get_job_as_user(user, remoteci_context, components_user_ids):
    job = remoteci_context.post('/api/v1/jobs',
                                data={'components': components_user_ids}).data
    job_id = job['job']['id']
    job = user.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200


def test_delete_job_as_user(user, job_user_id):
    job = user.get('/api/v1/jobs/%s' % job_user_id)
    job_etag = job.headers.get("ETag")

    job_delete = user.delete('/api/v1/jobs/%s' % job_user_id,
                             headers={'If-match': job_etag})
    assert job_delete.status_code == 204


def test_create_file_for_job_id(user, remoteci_context, components_user_ids):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()
        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }
        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        # create a job
        job = remoteci_context.post('/api/v1/jobs',
                                    data={'components': components_user_ids})
        job_id = job.data['job']['id']
        assert job.status_code == 201

        # create a file
        headers = {'DCI-JOB-ID': job_id,
                   'DCI-NAME': 'foobar'}
        file = user.post('/api/v1/files', headers=headers)
        file_id = file.data['file']['id']
        file = user.get('/api/v1/files/%s' % file_id).data
        assert file['file']['name'] == 'foobar'


@pytest.mark.usefixtures('file_job_user_id')
def test_get_file_by_job_id(user, job_user_id):
    url = '/api/v1/jobs/%s/files' % job_user_id

    # get file from job
    file_from_job = user.get(url)
    assert file_from_job.status_code == 200
    assert file_from_job.data['_meta']['count'] == 1


def test_get_results_by_job_id(user, job_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:
        mockito = mock.MagicMock()
        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 1
        }

        def get(a):
            return [True, six.StringIO(JUNIT)]

        mockito.head.return_value = head_result
        mockito.get = get
        mock_swift.return_value = mockito
        headers = {'DCI-JOB-ID': job_user_id,
                   'Content-Type': 'application/junit',
                   'DCI-MIME': 'application/junit',
                   'DCI-NAME': 'res_junit.xml'}

        user.post('/api/v1/files', headers=headers, data=JUNIT)

        # get file from job
        file_from_job = user.get('/api/v1/jobs/%s/results' % job_user_id)
        assert file_from_job.status_code == 200
        assert file_from_job.data['_meta']['count'] == 1
        assert file_from_job.data['results'][0]['total'] == 6
        assert len(file_from_job.data['results'][0]['testscases']) > 0
