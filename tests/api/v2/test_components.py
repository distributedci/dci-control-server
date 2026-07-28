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

import responses

from dci import dci_config


@responses.activate
def test_get_component_file_from_rhdl_user_team_in_RHEL_with_released_component(
    client_admin,
    hmac_client_team1,
    team1_remoteci,
    rhel_product,
    rhel_80_component,
):
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_composeinfo_url = (
        f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/.composeinfo"
    )

    responses.add(
        method=responses.GET,
        url=rhdl_composeinfo_url,
        status=302,
        headers={
            "Location": "https://wedontcare",
        },
    )
    responses.add(
        method=responses.HEAD,
        url=rhdl_composeinfo_url,
        status=302,
        headers={
            "Location": "https://wedontcare",
        },
    )

    r = hmac_client_team1.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/.composeinfo"
    )
    assert r.status_code == 302
    assert r.headers["Location"] is not None
    assert responses.assert_call_count(rhdl_composeinfo_url, 1) is True

    r = hmac_client_team1.head(
        f"/api/v2/components/{rhel_80_component['id']}/files/.composeinfo"
    )
    assert r.status_code == 302
    assert r.headers["Location"] is not None

    assert responses.assert_call_count(rhdl_composeinfo_url, 2) is True

    # delete product team permission
    r = client_admin.delete(
        "/api/v1/products/%s/teams/%s"
        % (rhel_product["id"], team1_remoteci["team_id"]),
    )
    assert r.status_code == 204

    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401

    r = hmac_client_team1.head(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401


@responses.activate
def test_get_files_list_from_rhdl_renames_files_list(
    hmac_client_team1,
    rhel_80_component,
):
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_files_list_url = f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/rhdl_files_list.json"
    responses.add(
        method=responses.GET,
        url=rhdl_files_list_url,
        status=302,
        headers={
            "Location": "https://wedontcare",
        },
    )

    r = hmac_client_team1.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/dci_files_list.json"
    )
    assert r.status_code == 302
    assert r.headers["Location"] is not None
    assert responses.assert_call_count(rhdl_files_list_url, 1) is True


@responses.activate
def test_get_component_file_from_rhdl_handles_404_with_bytes_message(
    hmac_client_team1,
    rhel_80_component,
):
    """Regression test for bytes serialization issue.

    When RHDL API returns a 404 error with a JSON error message as bytes,
    the DCIException should properly handle the bytes content and return
    a valid JSON response instead of raising a TypeError during JSON
    serialization.

    This reproduces the production traceback:
    TypeError: Object of type bytes is not JSON serializable
    """
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_file_url = (
        f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/images_list.yaml"
    )

    # Simulate RHDL API returning 404 with JSON error message as bytes
    # This is what happens in production when a file is not found
    error_response_body = (
        b'{\n  "status_code": "404",\n  '
        b'"message": "Error while heading file \'RHEL-10.2-updates-20260306.0/images_list.yaml\': '
        b'An error occurred"\n}\n'
    )

    responses.add(
        method=responses.GET,
        url=rhdl_file_url,
        status=404,
        body=error_response_body,
        content_type="application/json",
    )

    # This should not raise TypeError during JSON serialization
    r = hmac_client_team1.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/images_list.yaml"
    )

    # Should return 404 with a valid JSON response (not TypeError)
    assert r.status_code == 404
    # The response should be a valid JSON object
    response_data = r.data
    assert "status_code" in response_data
    assert "message" in response_data
    # Verify the message was extracted from the nested JSON
    assert (
        response_data["message"]
        == "Error while heading file 'RHEL-10.2-updates-20260306.0/images_list.yaml': An error occurred"
    )


@responses.activate
def test_get_component_file_from_rhdl_handles_500_with_bytes_message(
    hmac_client_team1,
    rhel_80_component,
):
    """Test that 500 errors with bytes content are also handled properly."""
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_file_url = (
        f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/test.txt"
    )

    error_response_body = b'{"status_code": "500", "message": "Internal server error"}'

    responses.add(
        method=responses.GET,
        url=rhdl_file_url,
        status=500,
        body=error_response_body,
        content_type="application/json",
    )

    r = hmac_client_team1.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/test.txt"
    )

    assert r.status_code == 500
    response_data = r.data
    assert "status_code" in response_data
    assert "message" in response_data
    assert response_data["message"] == "Internal server error"


@responses.activate
def test_get_component_file_from_rhdl_handles_404_json_without_message_field(
    hmac_client_team1,
    rhel_80_component,
):
    """Test that 404 errors with JSON but no 'message' field are handled.

    When the RHDL response is JSON but doesn't contain a 'message' field,
    the entire JSON object should be included in the error response.
    """
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_file_url = (
        f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/missing.txt"
    )

    error_response_body = b'{"status_code": "404", "error": "File not found"}'

    responses.add(
        method=responses.GET,
        url=rhdl_file_url,
        status=404,
        body=error_response_body,
        content_type="application/json",
    )

    r = hmac_client_team1.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/missing.txt"
    )

    assert r.status_code == 404
    response_data = r.data
    assert "status_code" in response_data
    assert "message" in response_data
    # When RHDL JSON has no "message" field, the entire JSON is used
    assert response_data["message"] == {"status_code": "404", "error": "File not found"}


def test_get_component_file_blocks_path_traversal(
    hmac_client_team1,
    rhel_80_component,
):
    test_cases = [
        "../etc/passwd",
        "./../etc/passwd",
        "dir/../../etc/passwd",
    ]
    for payload in test_cases:
        r = hmac_client_team1.get(
            f"/api/v2/components/{rhel_80_component['id']}/files/{payload}"
        )
        assert r.status_code == 400, f"Failed to block path traversal: {payload}"


def test_get_component_file_blocks_url_encoded_traversal(
    hmac_client_team1,
    rhel_80_component,
):
    test_cases = [
        "..%2Fetc%2Fpasswd",
        "%2e%2e%2Fetc%2Fpasswd",
        "%2e%2e/etc/passwd",
        "..%2F..%2Fetc%2Fpasswd",
        "%2e%2e%2F%2e%2e%2Fetc%2Fpasswd",
    ]
    for payload in test_cases:
        r = hmac_client_team1.get(
            f"/api/v2/components/{rhel_80_component['id']}/files/{payload}"
        )
        assert r.status_code == 400, f"Failed to block URL-encoded traversal: {payload}"


def test_get_component_file_blocks_double_url_encoded_traversal(
    hmac_client_team1,
    rhel_80_component,
):
    test_cases = [
        "%252e%252e%252Fetc%252Fpasswd",
        "%252e%252e%252F%252e%252e%252Fetc%252Fpasswd",
    ]
    for payload in test_cases:
        r = hmac_client_team1.get(
            f"/api/v2/components/{rhel_80_component['id']}/files/{payload}"
        )
        assert (
            r.status_code == 400
        ), f"Failed to block double-encoded traversal: {payload}"


def test_component_with_malicious_display_name_blocked(
    hmac_client_team1,
    rhel_80_component,
    engine,
):
    from dci.db import models2

    malicious_display_names = [
        "../../etc",
        "../component",
        "valid/../invalid",
        "path/with/slash",
    ]

    for display_name in malicious_display_names:
        with engine.begin() as conn:
            conn.execute(
                models2.Component.__table__.update()
                .where(models2.Component.id == rhel_80_component["id"])
                .values(display_name=display_name)
            )

        r = hmac_client_team1.get(
            f"/api/v2/components/{rhel_80_component['id']}/files/test.txt"
        )
        assert (
            r.status_code == 400
        ), f"Failed to block malicious display_name: {display_name}"
