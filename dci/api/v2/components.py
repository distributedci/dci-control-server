# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Red Hat, Inc
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

import os
import re

import flask
import logging
import requests

from dci.api.v2 import api
from dci.api.v1 import base
from dci.api.v1 import permissions
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.dci_config import CONFIG
from dci.db import models2
from dciauth.signature import HmacAuthBase

logger = logging.getLogger(__name__)


def _reject_url_encoded_characters(text: str) -> None:
    if re.search(r"%[0-9a-fA-F]{2}", text):
        raise dci_exc.DCIException("Request malformed: contains URL-encoded characters")


def _normalize_component_filepath(component_id: str, filepath: str) -> str:
    _reject_url_encoded_characters(filepath)

    component_id_filepath = os.path.join(component_id, filepath)
    normalized_component_id_filepath = os.path.normpath(
        "/" + component_id_filepath
    ).lstrip("/")

    if component_id_filepath != normalized_component_id_filepath:
        raise dci_exc.DCIException("Request malformed: filepath is invalid")

    return normalized_component_id_filepath


def get_component_file_from_rhdl(filepath, component):
    if filepath == "dci_files_list.json":
        filepath = "rhdl_files_list.json"

    _reject_url_encoded_characters(component.display_name)

    if "/" in component.display_name:
        raise dci_exc.DCIException(
            "Request malformed: display_name contains invalid characters"
        )

    normalized_rhdl_component_filepath = _normalize_component_filepath(
        os.path.join(component.display_name, "files"), filepath
    )

    rhdl_file_url = os.path.join(
        CONFIG["RHDL_API_URL"], "components", normalized_rhdl_component_filepath
    )
    auth = HmacAuthBase(
        access_key=CONFIG["RHDL_SERVICE_ACCOUNT_ACCESS_KEY"],
        secret_key=CONFIG["RHDL_SERVICE_ACCOUNT_SECRET_KEY"],
        region="us-east-1",
        service="api",
        service_key="aws4_request",
        algorithm="AWS4-HMAC-SHA256",
    )
    redirect = requests.get(
        rhdl_file_url,
        allow_redirects=False,
        auth=auth,
        timeout=CONFIG["REQUESTS_TIMEOUT"],
    )
    if redirect.status_code != 302:
        error_message = redirect.content
        try:
            content_json = redirect.json()
            if isinstance(content_json, dict) and "message" in content_json:
                error_message = content_json["message"]
            else:
                error_message = content_json
        except (requests.exceptions.JSONDecodeError, ValueError):
            if isinstance(error_message, bytes):
                error_message = error_message.decode("utf-8", errors="replace")

        raise dci_exc.DCIException(
            message=error_message, status_code=redirect.status_code
        )

    return flask.Response(None, 302, headers={"Location": redirect.headers["Location"]})


@api.route("/components/<uuid:c_id>/files/<path:filepath>", methods=["GET", "HEAD"])
@decorators.login_required
def get_component_file_from_rhdl_endpoint(user, c_id, filepath):
    component = base.get_resource_orm(models2.Component, c_id)
    permissions.verify_access_to_component(user, component)

    return get_component_file_from_rhdl(filepath, component)
