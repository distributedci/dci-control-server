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
from six.moves.urllib.parse import urlparse

import collections
import dci.common.exceptions as exceptions
import dci.common.utils as utils
import dci.db.models as models
import six
import voluptuous as v


# Url validator is not powerfull enough let unleash its power
@v.message('expected a URL', cls=v.UrlInvalid)
def Url(value):
    try:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise v.UrlInvalid("must have a URL scheme and host")
        return value
    except Exception:
        raise ValueError

VALID_STATUS_UPDATE = ['failure', 'success', 'killed', 'product-failure',
                       'deployment-failure']

VALID_RESOURCE_STATE = ['active', 'inactive', 'archived']

INVALID_LIST = 'not a valid list'
INVALID_UUID = 'not a valid uuid'
INVALID_JSON = 'not a valid json'
INVALID_STRING = 'not a valid string'
INVALID_URL = 'not a valid URL'
INVALID_PRIORITY = 'not a valid priority integer (must be beetween 0 and 1000)'

INVALID_TEAM = 'not a valid team id'
INVALID_TEST = 'not a valid test id'
INVALID_TOPIC = 'not a valid topic id'
INVALID_JOB_DEFINITION = 'not a valid jobdefinition id'
INVALID_REMOTE_CI = 'not a valid remoteci id'
INVALID_JOB = 'not a valid job id'
INVALID_JOB_STATE = 'not a valid jobstate id'
INVALID_ROLE = ('not a valid role (must be %s)' %
                ' or '.join(models.USER_ROLES))
INVALID_OFFSET = 'not a valid offset integer (must be greater than 0)'
INVALID_LIMIT = 'not a valid limit integer (must be greater than 0)'

INVALID_REQUIRED = 'required key not provided'
INVALID_OBJECT = 'not a valid object'
INVALID_STATUS_UPDATE = ('not a valid status update (must be %s)' %
                         ' or '.join(VALID_STATUS_UPDATE))
INVALID_RESOURCE_STATE = ('not a valid resource state (must be %s)' %
                          ' or '.join(VALID_RESOURCE_STATE))

UUID_FIELD = v.All(six.text_type, msg=INVALID_UUID)
DATA_FIELD = {v.Optional('data', default={}): dict}


class Schema(v.Schema):
    """Override voluptuous schema to return our own error"""

    error_messages = {
        'expected dict': INVALID_JSON,
        'expected unicode': INVALID_STRING,
        'expected str': INVALID_STRING,
        'expected a URL': INVALID_URL,
        'expected a dictionary': INVALID_OBJECT,
        'expected list': INVALID_LIST
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

split_coerce = v.Coerce(lambda s: s.split(','))
args = Schema({
    v.Optional('limit', default=None): v.All(v.Coerce(int), v.Range(0),
                                             msg=INVALID_LIMIT),
    v.Optional('offset', default=None): v.All(v.Coerce(int), v.Range(0),
                                              msg=INVALID_OFFSET),
    v.Optional('sort', default=[]): split_coerce,
    v.Optional('where', default=[]): split_coerce,
    v.Optional('embed', default=[]): split_coerce
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
role = schema_factory(base)

###############################################################################
#                                                                             #
#                                 Team schemas                                #
#                                                                             #
###############################################################################

team = utils.dict_merge(base, {
    v.Optional('country', default=None): six.text_type,
    v.Optional('email', default=None): six.text_type,
    v.Optional('notification', default=False): bool,
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

team = schema_factory(team)

###############################################################################
#                                                                             #
#                                 Test schemas                                #
#                                                                             #
###############################################################################

test = utils.dict_merge(base, DATA_FIELD, {
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

test = schema_factory(test)

###############################################################################
#                                                                             #
#                                 User schemas                                #
#                                                                             #
###############################################################################

user = utils.dict_merge(base, {
    'password': six.text_type,
    v.Optional('role'): v.Any(*models.USER_ROLES, msg=INVALID_ROLE),
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

user = schema_factory(user)

###############################################################################
#                                                                             #
#                              Component schemas                              #
#                                                                             #
###############################################################################

component = utils.dict_merge(base, DATA_FIELD, {
    v.Optional('title', default=None): six.text_type,
    v.Optional('message', default=None): six.text_type,
    v.Optional('canonical_project_name', default=None): six.text_type,
    # True if the component can be exported to non US countries.
    v.Optional('export_control', default=False): bool,
    v.Optional('url', default=None): Url(),
    'type': six.text_type,
    'topic_id': v.Any(UUID_FIELD, msg=INVALID_TOPIC),
    v.Optional('active', default=True): bool,
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

component_put = {
    v.Optional('export_control'): bool,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

component = DCISchema(schema_factory(component).post,
                      Schema(component_put))

###############################################################################
#                                                                             #
#                           Job Definition schemas                            #
#                                                                             #
###############################################################################

jobdefinition = utils.dict_merge(base, {
    v.Optional('priority', default=0): v.All(
        v.Coerce(int), v.Range(min=0, max=1000), msg=INVALID_PRIORITY
    ),
    'topic_id': v.Any(UUID_FIELD, msg=INVALID_TOPIC),
    v.Optional('active', default=True): bool,
    v.Optional('comment', default=None): six.text_type,
    v.Optional('component_types', default=[]): list,
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

jobdefinition_put = {
    v.Optional('comment'): six.text_type,
    v.Optional('active'): bool,
    v.Optional('component_types', default=[]): list,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

jobdefinition = DCISchema(schema_factory(jobdefinition).post,
                          Schema(jobdefinition_put))

###############################################################################
#                                                                             #
#                             Remote CI schemas                               #
#                                                                             #
###############################################################################

remoteci = utils.dict_merge(base, DATA_FIELD, {
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
    v.Optional('active', default=True): bool,
    v.Optional('allow_upgrade_job', default=False): bool,
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

remoteci_put = {
    v.Optional('name'): six.text_type,
    v.Optional('data'): dict,
    v.Optional('team_id'): v.Any(UUID_FIELD, msg=INVALID_TEAM),
    v.Optional('active'): bool,
    v.Optional('allow_upgrade_job'): bool,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

remoteci = DCISchema(schema_factory(remoteci).post, Schema(remoteci_put))

###############################################################################
#                                                                             #
#                                Job schemas                                  #
#                                                                             #
###############################################################################

job = {
    'jobdefinition_id': v.Any(UUID_FIELD, msg=INVALID_JOB_DEFINITION),
    'remoteci_id': v.Any(UUID_FIELD, msg=INVALID_REMOTE_CI),
    'team_id': v.Any(UUID_FIELD, msg=INVALID_TEAM),
    'components': list,
    v.Optional('comment', default=None): six.text_type,
    v.Optional('previous_job_id', default=None): v.Any(UUID_FIELD,
                                                       msg=INVALID_JOB),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
}

job_put = {
    v.Optional('comment'): six.text_type,
    v.Optional('status'): v.Any(*VALID_STATUS_UPDATE,
                                msg=INVALID_STATUS_UPDATE),
    v.Optional('configuration'): dict,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

job = DCISchema(schema_factory(job).post, Schema(job_put))

job_schedule = {
    'remoteci_id': v.Any(UUID_FIELD, msg=INVALID_REMOTE_CI),
    'topic_id': v.Any(UUID_FIELD, msg=INVALID_TOPIC)
}

job_schedule = schema_factory(job_schedule)


job_upgrade = {
    'job_id': v.Any(UUID_FIELD, msg=INVALID_JOB)
}

job_upgrade = schema_factory(job_upgrade)


job_schedule_template = {
    'remoteci_id': v.Any(UUID_FIELD, msg=INVALID_REMOTE_CI),
    'topic_id': v.Any(UUID_FIELD, msg=INVALID_TOPIC),

}

job_schedule_template = schema_factory(job_schedule_template)

job_search = {
    'jobdefinition_id': v.Any(UUID_FIELD, msg=INVALID_JOB_DEFINITION),
    # todo(yassine): validate configuration structure
    'configuration': dict
}

job_search = schema_factory(job_search)

###############################################################################
#                                                                             #
#                             Job State schemas                               #
#                                                                             #
###############################################################################

jobstate = {
    'status': six.text_type,
    'job_id': v.Any(UUID_FIELD, msg=INVALID_JOB),
    v.Optional('comment', default=None): six.text_type,
}

jobstate = schema_factory(jobstate)

###############################################################################
#                                                                             #
#                                File schemas                                 #
#                                                                             #
###############################################################################

file = utils.dict_merge(base, {
    v.Optional('content', default=''): six.text_type,
    v.Optional('md5', default=None): six.text_type,
    v.Optional('mime', default=None): six.text_type,
    v.Optional('jobstate_id', default=None): v.Any(UUID_FIELD,
                                                   msg=INVALID_JOB_STATE),
    v.Optional('job_id', default=None): v.Any(UUID_FIELD,
                                              msg=INVALID_JOB),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

file = schema_factory(file)

###############################################################################
#                                                                             #
#                                Topic schemas                                #
#                                                                             #
###############################################################################

topic = utils.dict_merge(base, {
    v.Optional('label', default=None): six.text_type,
    v.Optional('next_topic', default=None): v.Any(UUID_FIELD,
                                                  msg=INVALID_JOB),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

topic = schema_factory(topic)

###############################################################################
#                                                                             #
#                              Search schemas                                 #
#                                                                             #
###############################################################################

search = {
    'pattern': six.text_type,
    v.Optional('refresh', default=False): bool,
}

search = schema_factory(search)

###############################################################################
#                                                                             #
#                               Audit schemas                                 #
#                                                                             #
###############################################################################

audit = {
    v.Optional('limit', default=10): int
}

audit = schema_factory(audit)

###############################################################################
#                                                                             #
#                                Issues schemas                               #
#                                                                             #
###############################################################################

issue = {
    'url': Url(),
}

issue = schema_factory(issue)

###############################################################################
#                                                                             #
#                                Metas schemas                                #
#                                                                             #
###############################################################################

meta = {
    'name': six.text_type,
    'value': six.text_type
}

meta_put = {
    v.Optional('name'): six.text_type,
    v.Optional('value'): six.text_type
}

meta = DCISchema(schema_factory(meta).post, Schema(meta_put))
