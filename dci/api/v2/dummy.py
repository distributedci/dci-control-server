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

import flask

from dci.api.v2 import api
from dci.api.v1.notifications import publish
import logging

logger = logging.getLogger(__name__)


@api.route("/pubmsg", methods=["GET"])
def pubmsg():
    publish({"event": "pubmsg", "msg": "toto"})

    return flask.Response("Processing", 200, content_type="text/plain")
