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
from __future__ import unicode_literals

import dci.common.schemas as schemas
import tests.common.utils as utils

import flask
import voluptuous


def test_validation_error_handling(app):
    schema = schemas.Schema({voluptuous.Required('id'): str})
    app.add_url_rule('/test_validation_handling', view_func=lambda: schema({}))

    client = app.test_client()
    resp = client.get('/test_validation_handling')
    assert resp.status_code == 400
    assert flask.json.loads(resp.data) == {
        'status_code': 400,
        'message': 'Request malformed',
        'payload': {
            'errors': {'id': 'required key not provided'}
        }
    }


class BaseSchemaTesting(utils.SchemaTesting):

    data = dict([utils.NAME])

    def test_post_extra_data(self):
        super(BaseSchemaTesting, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(BaseSchemaTesting, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        super(BaseSchemaTesting, self).test_post_invalid_data(
            dict([utils.INVALID_NAME]), dict([utils.INVALID_NAME_ERROR])
        )

    def test_post(self):
        super(BaseSchemaTesting, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(BaseSchemaTesting, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])

        super(BaseSchemaTesting, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(BaseSchemaTesting, self).test_put(self.data, self.data)


class TestComponentType(BaseSchemaTesting):
    schema = schemas.componenttype


class TestTeam(utils.SchemaTesting):
    schema = schemas.team
    data = dict([utils.NAME, utils.COUNTRY, utils.EMAIL, utils.NOTIF])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestTeam, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTeam, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTeam.generate_invalids_and_errors()
        super(TestTeam, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestTeam, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        invalids, errors = TestTeam.generate_invalids_and_errors()
        super(TestTeam, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestTeam.generate_invalids_and_errors()
        super(TestTeam, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestTeam, self).test_put(self.data, self.data)


class TestRole(BaseSchemaTesting):
    schema = schemas.role


class TestTest(utils.SchemaTesting):
    schema = schemas.test
    data = dict([utils.NAME, utils.TEAM])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_DATA,
                         utils.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR,
                       utils.INVALID_TEAM_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestTest, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'team_id')
        super(TestTest, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestTest, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestTest, self).test_put(self.data, data_expected)


class TestUser(utils.SchemaTesting):
    schema = schemas.user
    data = dict([utils.NAME, utils.PASSWORD, utils.TEAM, utils.ROLE])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                         utils.INVALID_TEAM, utils.INVALID_ROLE])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR, utils.INVALID_ROLE_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestUser, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'password', 'team_id')
        super(TestUser, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestUser.generate_invalids_and_errors()
        super(TestUser, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestUser, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestUser, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestUser.generate_invalids_and_errors()
        super(TestUser, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestUser, self).test_put(self.data, self.data)


class TestComponent(utils.SchemaTesting):
    schema = schemas.component
    data = dict([utils.NAME, utils.TYPE, utils.TOPIC])

    @staticmethod
    def generate_optionals():
        return dict([('title', None), ('message', None), ('url', None),
                     ('data', {}), ('canonical_project_name', None),
                     ('export_control', False), ('active', True)])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = []
        errors = []
        for field in ['title', 'message', 'canonical_project_name', 'type']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, utils.INVALID_DATA,
                         utils.INVALID_TOPIC] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR,
                       utils.INVALID_DATA_ERROR,
                       utils.INVALID_TOPIC_ERROR] + errors)

        return invalids, errors

    def test_post_extra_data(self):
        super(TestComponent, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'type', 'topic_id')
        super(TestComponent, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestComponent.generate_invalids_and_errors()
        super(TestComponent, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         TestComponent.generate_optionals())
        super(TestComponent, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestJobDefinition(utils.SchemaTesting):
    schema = schemas.jobdefinition
    data = dict([utils.NAME, utils.TOPIC])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, ('priority', -1),
                         utils.INVALID_TOPIC])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_PRIORITY_ERROR,
                       utils.INVALID_TOPIC_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'priority': 10})
        super(TestJobDefinition, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'topic_id')
        super(TestJobDefinition, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobDefinition.generate_invalids_and_errors()
        super(TestJobDefinition, self).test_post_invalid_data(invalids, errors)
        invalids['priority'] = 1001
        super(TestJobDefinition, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(
            self.data,
            {'priority': 0, 'active': True, 'comment': None,
             'component_types': []})
        super(TestJobDefinition, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestRemoteCI(utils.SchemaTesting):
    schema = schemas.remoteci
    data = dict([utils.NAME, utils.TEAM, utils.ACTIVE,
                 utils.ALLOW_UPGRADE_JOB])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEAM_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestRemoteCI, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'team_id')
        super(TestRemoteCI, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestRemoteCI.generate_invalids_and_errors()
        super(TestRemoteCI, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestRemoteCI, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestRemoteCI, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestRemoteCI.generate_invalids_and_errors()
        super(TestRemoteCI, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        super(TestRemoteCI, self).test_put(self.data, self.data)


class TestJob(utils.SchemaTesting):
    schema = schemas.job
    data = dict([utils.JOB_DEFINITION, utils.REMOTE_CI, utils.TEAM,
                 utils.COMPONENTS, utils.PREVIOUS_JOB_ID])
    data_put = dict([('status', 'success'), utils.COMMENT,
                     utils.CONFIGURATION])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_JOB_DEFINITION,
                         utils.INVALID_REMOTE_CI, utils.INVALID_TEAM,
                         utils.INVALID_COMPONENTS])
        errors = dict([utils.INVALID_REMOTE_CI_ERROR,
                       utils.INVALID_JOB_DEFINITION_ERROR,
                       utils.INVALID_TEAM_ERROR,
                       utils.INVALID_COMPONENTS_ERROR])
        return invalids, errors

    @staticmethod
    def generate_invalids_and_errors_put():
        invalids = dict([utils.INVALID_COMMENT, utils.STATUS])
        errors = dict([utils.INVALID_COMMENT_ERROR,
                       ('status', schemas.INVALID_STATUS_UPDATE)])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'comment': 'some comment'})
        super(TestJob, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('jobdefinition_id',
                                       'remoteci_id', 'team_id', 'components')
        super(TestJob, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJob.generate_invalids_and_errors()
        super(TestJob, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'comment': None})
        super(TestJob, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestJob, self).test_put_extra_data(self.data_put)

    def test_put_invalid_data(self):
        invalids, errors = TestJob.generate_invalids_and_errors_put()
        super(TestJob, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        super(TestJob, self).test_put(self.data_put, self.data_put)


class TestJobSchedule(utils.SchemaTesting):
    schema = schemas.job_schedule
    data = dict([utils.REMOTE_CI, utils.TOPIC])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_REMOTE_CI, utils.INVALID_TOPIC])
        errors = dict([utils.INVALID_REMOTE_CI_ERROR,
                       utils.INVALID_TOPIC_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestJobSchedule, self).test_post(self.data, self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('remoteci_id', 'topic_id')
        super(TestJobSchedule, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobSchedule.generate_invalids_and_errors()
        super(TestJobSchedule, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJobSchedule, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestJobSearch(utils.SchemaTesting):
    schema = schemas.job_search
    data = dict([utils.JOB_DEFINITION, utils.CONFIGURATION])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_JOB_DEFINITION,
                         utils.INVALID_CONFIGURATION])
        errors = dict([utils.INVALID_JOB_DEFINITION_ERROR,
                       utils.INVALID_CONFIGURATION_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestJobSearch, self).test_post(self.data, self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('jobdefinition_id', 'configuration')
        super(TestJobSearch, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobSearch.generate_invalids_and_errors()
        super(TestJobSearch, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJobSearch, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestIssue(utils.SchemaTesting):
    schema = schemas.issue
    data = dict([utils.URL])

    @staticmethod
    def generate_invalids_and_errors():
        status_invalid, status_error = utils.generate_invalid_string('url')

        invalids = dict([utils.INVALID_URL, status_invalid])
        errors = dict([utils.INVALID_URL_ERROR, status_error])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'extra': 'some comment'})
        super(TestIssue, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('url')
        super(TestIssue, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestIssue.generate_invalids_and_errors()
        super(TestIssue, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestIssue, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestMeta(utils.SchemaTesting):
    schema = schemas.meta
    data = dict([utils.NAME, utils.VALUE])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME,
                         utils.INVALID_VALUE])
        errors = dict([utils.INVALID_NAME_ERROR,
                       utils.INVALID_VALUE_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'extra': 'some comment'})
        super(TestMeta, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'value')
        super(TestMeta, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestMeta.generate_invalids_and_errors()
        super(TestMeta, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestMeta, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestMeta, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestMeta.generate_invalids_and_errors()
        super(TestMeta, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        super(TestMeta, self).test_put(self.data, self.data)


class TestJobState(utils.SchemaTesting):
    schema = schemas.jobstate
    data = dict([utils.STATUS, utils.JOB])

    @staticmethod
    def generate_invalids_and_errors():
        status_invalid, status_error = utils.generate_invalid_string('status')

        invalids = dict([utils.INVALID_JOB, status_invalid])
        errors = dict([utils.INVALID_JOB_ERROR, status_error])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'comment': 'some comment'})
        super(TestJobState, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('status', 'job_id')
        super(TestJobState, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobState.generate_invalids_and_errors()
        super(TestJobState, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        pass
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'comment': None})
        super(TestJobState, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestJobState, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestJobState.generate_invalids_and_errors()
        super(TestJobState, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'comment': None})
        super(TestJobState, self).test_put(self.data, data_expected)


# todo(yassine): this will be re activated when we will verify
# files api call's headers with voluptuous
class LolTestFile(utils.SchemaTesting):
    schema = schemas.file
    data = dict([utils.NAME, utils.CONTENT, utils.JOB_STATE, utils.JOB])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = []
        errors = []

        for field in ['content', 'md5', 'mime']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, utils.INVALID_JOB_STATE] +
                        invalids)
        errors = dict(
            [utils.INVALID_NAME_ERROR, utils.INVALID_JOB_STATE_ERROR] +
            errors
        )
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'mime': 'mime', 'md5': 'md5'})
        super(LolTestFile, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(LolTestFile, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = LolTestFile.generate_invalids_and_errors()
        super(LolTestFile, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         {'mime': None, 'md5': None})
        super(LolTestFile, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(LolTestFile, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = LolTestFile.generate_invalids_and_errors()
        super(LolTestFile, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         {'mime': None, 'md5': None})
        super(LolTestFile, self).test_put(self.data, data_expected)


class TestTopic(utils.SchemaTesting):
    schema = schemas.topic
    data = dict([utils.NAME, utils.LABEL, utils.NEXT_TOPIC])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestTopic, self).test_post(self.data, self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTopic, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTopic.generate_invalids_and_errors()
        super(TestTopic, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestTopic, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestArgs(object):
    data = {
        'limit': '50',
        'offset': '10',
        'sort': 'field_1,field_2',
        'where': 'field_1:value_1,field_2:value_2',
        'embed': 'resource_1,resource_2'
    }

    data_expected = {
        'limit': 50,
        'offset': 10,
        'sort': ['field_1', 'field_2'],
        'where': ['field_1:value_1', 'field_2:value_2'],
        'embed': ['resource_1', 'resource_2']
    }

    def test_extra_args(self):
        extra_data = utils.dict_merge(self.data, {'foo': 'bar'})
        assert schemas.args(extra_data) == self.data_expected

    def test_default_args(self):
        expected = {
            'limit': None,
            'offset': None,
            'sort': [],
            'where': [],
            'embed': []
        }
        assert schemas.args({}) == expected

    def test_invalid_args(self):
        errors = {'limit': schemas.INVALID_LIMIT,
                  'offset': schemas.INVALID_OFFSET}

        data = {'limit': -1, 'offset': -1}
        utils.invalid_args(data, errors)
        data = {'limit': 'foo', 'offset': 'bar'}
        utils.invalid_args(data, errors)

    def test_args(self):
        assert schemas.args(self.data) == self.data_expected
