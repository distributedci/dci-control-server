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
from __future__ import unicode_literals

import dci.server.common.schemas as schemas
import dci.server.tests.schemas.utils as utils
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
    schema = schemas.component_type


class TestTeam(BaseSchemaTesting):
    schema = schemas.team


class TestRole(BaseSchemaTesting):
    schema = schemas.role


class TestTest(utils.SchemaTesting):
    schema = schemas.test
    data = dict([utils.NAME])

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestTest, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTest, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_DATA])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR])

        super(TestTest, self).test_post_invalid_data(data, errors)

    def test_post(self):
        super(TestTest, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestTest, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_DATA])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR])
        super(TestTest, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(TestTest, self).test_put(self.data, self.data)


class TestUser(utils.SchemaTesting):
    TEAM = 'team', utils.ID[1]
    INVALID_TEAM = 'team', utils.INVALID_ID
    INVALID_TEAM_ERROR = 'team', schemas.INVALID_TEAM

    schema = schemas.user
    data = dict([utils.NAME, utils.PASSWORD, TEAM])

    def test_post_extra_data(self):
        super(TestUser, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'password', 'team')
        super(TestUser, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                     self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR])

        super(TestUser, self).test_post_invalid_data(data, errors)

    def test_post(self):
        super(TestUser, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestUser, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                     self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR])

        super(TestUser, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(TestUser, self).test_put(self.data, self.data)


class TestComponent(utils.SchemaTesting):
    COMPONENTTYPE = 'componenttype', utils.ID[1]
    INVALID_COMPONENTTYPE = 'componenttype', utils.INVALID_ID
    INVALID_COMPONENTTYPE_ERROR = ('componenttype',
                                   schemas.INVALID_COMPONENT_TYPE)

    schema = schemas.component
    data = dict([utils.NAME, COMPONENTTYPE])

    @staticmethod
    def generate_optionals():
        return dict([('sha', utils.text_type), ('title', utils.text_type),
                     ('message', utils.text_type), ('git', utils.text_type),
                     ('ref', utils.text_type),
                     ('canonical_project_name', utils.text_type)])

    @staticmethod
    def generate_optionals_errors():
        invalids = []
        errors = []
        for field in ['sha', 'title', 'message', 'git', 'ref',
                      'canonical_project_name']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)
        return invalids, errors

    def test_post_extra_data(self):
        super(TestComponent, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'componenttype')
        super(TestComponent, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestComponent.generate_optionals_errors()

        data = dict([utils.INVALID_NAME, self.INVALID_COMPONENTTYPE,
                     utils.INVALID_DATA] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR,
                       self.INVALID_COMPONENTTYPE_ERROR,
                       utils.INVALID_DATA_ERROR] + errors)

        super(TestComponent, self).test_post_invalid_data(data, errors)

    def test_post(self):
        data_expected = utils.dict_merge(self.data)
        super(TestComponent, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestComponent, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestComponent.generate_optionals_errors()
        data = dict([utils.INVALID_NAME, self.INVALID_COMPONENTTYPE,
                     utils.INVALID_DATA, utils.INVALID_URL] + invalids)

        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR,
                       self.INVALID_COMPONENTTYPE_ERROR,
                       utils.INVALID_URL_ERROR] + errors)

        super(TestComponent, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(TestComponent, self).test_put(self.data, self.data)
