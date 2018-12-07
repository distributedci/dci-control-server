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
import hashlib
import itertools
import uuid

import flask
import six

from dci.common import exceptions
from sqlalchemy.engine import result
from werkzeug.routing import BaseConverter, ValidationError


def read(file_path, chunk_size=None, mode='rb'):
    chunk_size = chunk_size or 1024 ** 2  #  1MB
    with open(file_path, mode) as f:
        for chunk in iter(lambda: f.read(chunk_size) or None, None):
            yield chunk


class UUIDConverter(BaseConverter):

    def to_python(self, value):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError()

    def to_url(self, values):
        return str(values)


class JSONEncoder(flask.json.JSONEncoder):
    """Default JSON encoder."""
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, result.RowProxy):
            return dict(o)
        elif isinstance(o, result.ResultProxy):
            return list(o)
        elif isinstance(o, uuid.UUID):
            return str(o)


def gen_uuid():
    return str(uuid.uuid4())


def gen_etag():
    """Generate random etag based on MD5."""

    my_salt = gen_uuid()
    if six.PY2:
        my_salt = my_salt.decode('utf-8')
    elif six.PY3:
        my_salt = my_salt.encode('utf-8')
    md5 = hashlib.md5()
    md5.update(my_salt)
    return md5.hexdigest()


def check_and_get_etag(headers):
    if_match_etag = headers.get('If-Match')
    if not if_match_etag:
        raise exceptions.DCIException("'If-match' header must be provided",
                                      status_code=412)
    return if_match_etag


def dict_merge(*dict_list):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.
    '''
    result = collections.defaultdict(dict)
    dicts_items = itertools.chain(*[six.iteritems(d or {}) for d in dict_list])

    for key, value in dicts_items:
        src = result[key]
        if isinstance(src, dict) and isinstance(value, dict):
            result[key] = dict_merge(src, value)
        elif isinstance(src, dict) or isinstance(src, six.text_type):
            result[key] = value
        elif hasattr(src, '__iter__') and hasattr(value, '__iter__'):
            result[key] += value
        else:
            result[key] = value

    return dict(result)
