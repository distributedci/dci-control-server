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

from __future__ import unicode_literals
from dci import dci_config


def test_get_component_file_from_rhdl_user_team_in_RHEL_with_released_component(
    admin,
    remoteci_context,
    remoteci_user,
    rhel_product,
    rhel_80_component,
):
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]

    r = remoteci_context.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/.composeinfo"
    )
    assert r.status_code == 302
    assert (
        r.headers["Location"]
        == f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/.composeinfo"
    )

    r = remoteci_context.head(
        f"/api/v2/components/{rhel_80_component['id']}/files/.composeinfo"
    )
    assert r.status_code == 302
    assert (
        r.headers["Location"]
        == f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/.composeinfo"
    )

    # delete product team permission
    r = admin.delete(
        "/api/v1/products/%s/teams/%s" % (rhel_product["id"], remoteci_user["team_id"]),
    )
    assert r.status_code == 204

    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401

    r = remoteci_context.head(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401
