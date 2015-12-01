# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

import collections
import dci.server.common.exceptions as exceptions
import dci.server.utils as utils
import six
import six.moves.urllib as urllib
import voluptuous as v


# Url validator is not powerfull enough let unleash its power
@v.message('expected a URL', cls=v.UrlInvalid)
def Url(value):
    try:
        parsed = urllib.urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise v.UrlInvalid("must have a URL scheme and host")
        return value
    except Exception:
        raise ValueError

INVALID_UUID = 'not a valid uuid'
INVALID_JSON = 'not a valid json'
INVALID_STRING = 'not a valid string'
INVALID_URL = 'not a valid URL'
INVALID_PRIORITY = 'not a valid priority integer (must be beetween 0 and 1000)'

INVALID_TEAM = 'not a valid team id'
INVALID_COMPONENT_TYPE = 'not a valid componenttype id'
INVALID_TEST = 'not a valid test id'
INVALID_JOB_DEFINITION = 'not a valid jobdefinition id'
INVALID_REMOTE_CI = 'not a valid remoteci id'
INVALID_JOB = 'not a valid job id'
INVALID_JOB_STATE = 'not a valid jobstate id'

INVALID_OFFSET = 'not a valid offset integer (must be greater than 0)'
INVALID_LIMIT = 'not a valid limit integer (must be greater than 0)'

INVALID_REQUIRED = 'required key not provided'
INVALID_OBJECT = 'not a valid object'

UUID_FIELD = v.All(six.text_type, msg=INVALID_UUID)
DATA_FIELD = {v.Optional('data', default={}): dict}


class Schema(v.Schema):
    """Override voluptuous schema to return our own error"""

    error_messages = {
        'expected dict': INVALID_JSON,
        'expected unicode': INVALID_STRING,
        'expected str': INVALID_STRING,
        'expected a URL': INVALID_URL,
        'expected a dictionary': INVALID_OBJECT
    }

    def __call__(self, data):
        def format_error(error):
            msg = error.error_message
            error.error_message = self.error_messages.get(msg, msg)
            if error.path:
                path = six.text_type(error.path.pop())
                return {path: format_error(error)}
            else:
                return error.error_message

        try:
            return super(Schema, self).__call__(data)
        except v.MultipleInvalid as exc:
            errors = format_error(exc.errors.pop())
            for error in exc.errors:
                errors = utils.dict_merge(errors, format_error(error))
            raise exceptions.DCIException('Request malformed',
                                          {'errors': errors})


DCISchema = collections.namedtuple('DCISchema', ['post', 'put'])


def schema_factory(schema):
    schema_post = {}

    for key, value in six.iteritems(schema):
        if not isinstance(key, v.Marker):
            key = v.Required(key)
        schema_post[key] = value

    return DCISchema(Schema(schema_post), Schema(schema))

###############################################################################
#                                                                             #
#                                 Args schemas                                #
#                                                                             #
###############################################################################

split = lambda string: string.split(',')

args = Schema({
    v.Optional('limit', default=20): v.All(v.Coerce(int), v.Range(0),
                                           msg=INVALID_LIMIT),
    v.Optional('offset', default=0): v.All(v.Coerce(int), v.Range(0),
                                           msg=INVALID_OFFSET),
    v.Optional('sort', default=[]): v.Coerce(split),
    v.Optional('where', default=[]): v.Coerce(split),
    v.Optional('embed', default=[]): v.Coerce(split)
}, extra=v.REMOVE_EXTRA)

###############################################################################
#                                                                             #
#                                 Base schemas                                #
#                                                                             #
###############################################################################

base = {
    'name': six.text_type,
}


componenttype = schema_factory(base)
team = schema_factory(base)
role = schema_factory(base)

###############################################################################
#                                                                             #
#                                 Test schemas                                #
#                                                                             #
###############################################################################

test = schema_factory(utils.dict_merge(base, DATA_FIELD))

###############################################################################
#                                                                             #
#                                 User schemas                                #
#                                                                             #
###############################################################################

user = utils.dict_merge(base, {
    'password': six.text_type,
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM)
})

user = schema_factory(user)

###############################################################################
#                                                                             #
#                              Component schemas                              #
#                                                                             #
###############################################################################

component = utils.dict_merge(base, DATA_FIELD, {
    v.Optional('sha', default=None): six.text_type,
    v.Optional('title', default=None): six.text_type,
    v.Optional('message', default=None): six.text_type,
    v.Optional('git', default=None): six.text_type,
    v.Optional('ref', default=None): six.text_type,
    v.Optional('canonical_project_name', default=None): six.text_type,
    v.Optional('url', default=None): Url(),
    'componenttype_id': v.Any(UUID_FIELD, msg=INVALID_COMPONENT_TYPE)
})

component = schema_factory(component)

###############################################################################
#                                                                             #
#                           Job Definition schemas                            #
#                                                                             #
###############################################################################

jobdefinition = utils.dict_merge(base, {
    'test_id': v.Any(UUID_FIELD, msg=INVALID_TEST),
    v.Optional('priority', default=0): v.All(
        int, v.Range(min=0, max=1000), msg=INVALID_PRIORITY
    )
})

jobdefinition = schema_factory(jobdefinition)

###############################################################################
#                                                                             #
#                             Remote CI schemas                               #
#                                                                             #
###############################################################################

remoteci = utils.dict_merge(base, DATA_FIELD, {
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
})

remoteci = schema_factory(remoteci)

###############################################################################
#                                                                             #
#                                Job schemas                                  #
#                                                                             #
###############################################################################

job = {
    'jobdefinition_id': v.Any(UUID_FIELD, msg=INVALID_JOB_DEFINITION),
    'remoteci_id': v.Any(UUID_FIELD, msg=INVALID_REMOTE_CI),
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM)
}

job = schema_factory(job)

###############################################################################
#                                                                             #
#                             Job State schemas                               #
#                                                                             #
###############################################################################

jobstate = {
    'status': six.text_type,
    'job_id': v.Any(UUID_FIELD, msg=INVALID_JOB),
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
    v.Optional('comment'): six.text_type,
}

jobstate = schema_factory(jobstate)

###############################################################################
#                                                                             #
#                                File schemas                                 #
#                                                                             #
###############################################################################

file = utils.dict_merge(base, {
    'content': six.text_type,
    v.Optional('md5', default=None): six.text_type,
    v.Optional('mime', default=None): six.text_type,
    'jobstate_id': v.Any(UUID_FIELD, msg=INVALID_JOB_STATE),
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
})

file = schema_factory(file)

###############################################################################
#                                                                             #
#                              Search schemas                                 #
#                                                                             #
###############################################################################

search = {'pattern': six.text_type}

search = schema_factory(search)
