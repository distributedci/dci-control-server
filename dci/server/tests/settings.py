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

from dci.server.settings import *  # noqa
import os
import uuid

SQLALCHEMY_DATABASE_URI = "postgresql:///%s?host=%s" % (
    uuid.uuid4(), os.path.abspath(os.environ['DCI_DB_DIR'])
)

# detect if we are using docker_compose
if os.environ.get('DB_PORT'):
    import dci.server.settings
    SQLALCHEMY_DATABASE_URI = dci.server.settings.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI += "_test"
