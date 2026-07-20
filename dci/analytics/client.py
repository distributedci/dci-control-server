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

import requests
import time

from dci.auth import encode_service_jwt
from dci.common.exceptions import DCIException
from dci.dci_config import CONFIG

_jwt_token_cache = {"token": None, "expires_at": 0.0}
_JWT_CACHE_REFRESH_BUFFER_SECONDS = 30


def _get_analytics_jwt_token():
    now = time.monotonic()
    if (
        _jwt_token_cache["token"] is not None
        and now + _JWT_CACHE_REFRESH_BUFFER_SECONDS < _jwt_token_cache["expires_at"]
    ):
        return _jwt_token_cache["token"]

    secret = CONFIG["ANALYTICS_JWT_SECRET"]
    if not secret:
        raise DCIException("ANALYTICS_JWT_SECRET must not be empty")

    token = encode_service_jwt(
        secret,
        CONFIG["ANALYTICS_JWT_AUDIENCE"],
        CONFIG["ANALYTICS_JWT_ISSUER"],
        CONFIG["ANALYTICS_JWT_TTL_SECONDS"],
    )
    _jwt_token_cache["token"] = token
    _jwt_token_cache["expires_at"] = now + CONFIG["ANALYTICS_JWT_TTL_SECONDS"]
    return token


def analytics_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % _get_analytics_jwt_token(),
    }


def analytics_request(method, path, **kwargs):
    url = "%s%s" % (CONFIG["ANALYTICS_URL"], path)
    a_headers = analytics_headers()
    if "headers" in kwargs:
        kwargs["headers"].update(a_headers)
    else:
        kwargs["headers"] = a_headers
    if "timeout" not in kwargs:
        kwargs["timeout"] = CONFIG["REQUESTS_TIMEOUT"]
    return requests.request(method, url, **kwargs)
