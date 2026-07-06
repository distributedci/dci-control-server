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

import mock
import pytest

import dci.common.exceptions as dci_exc
from dci.analytics import client
from dci.dci_config import CONFIG

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-token",
}


def _reset_jwt_token_cache():
    client._jwt_token_cache["token"] = None
    client._jwt_token_cache["expires_at"] = 0.0


@mock.patch("dci.analytics.client.encode_service_jwt", return_value="token-1")
def test_analytics_jwt_token_is_cached(mock_encode_service_jwt):
    _reset_jwt_token_cache()

    headers_1 = client.analytics_headers()
    headers_2 = client.analytics_headers()

    mock_encode_service_jwt.assert_called_once()
    assert headers_1 == headers_2
    assert headers_1["Authorization"] == "Bearer token-1"


@mock.patch(
    "dci.analytics.client.encode_service_jwt", side_effect=["token-1", "token-2"]
)
@mock.patch("dci.analytics.client.time.monotonic")
def test_analytics_jwt_token_is_regenerated_after_cache_expiry(
    mock_monotonic, mock_encode_service_jwt
):
    _reset_jwt_token_cache()
    # Refresh when now + buffer >= expires_at, i.e. at TTL - buffer
    refresh_at = (
        CONFIG["ANALYTICS_JWT_TTL_SECONDS"] - client._JWT_CACHE_REFRESH_BUFFER_SECONDS
    )
    mock_monotonic.side_effect = [0.0, float(refresh_at)]

    headers_1 = client.analytics_headers()
    headers_2 = client.analytics_headers()

    assert mock_encode_service_jwt.call_count == 2
    assert headers_1["Authorization"] == "Bearer token-1"
    assert headers_2["Authorization"] == "Bearer token-2"


@mock.patch.dict(CONFIG, {"ANALYTICS_JWT_SECRET": ""})
def test_analytics_jwt_secret_must_not_be_empty():
    _reset_jwt_token_cache()

    with pytest.raises(
        dci_exc.DCIException, match="ANALYTICS_JWT_SECRET must not be empty"
    ):
        client.analytics_headers()


@mock.patch("dci.analytics.client.requests.request")
@mock.patch(
    "dci.analytics.client.analytics_headers", return_value=DEFAULT_HEADERS.copy()
)
def test_analytics_request_default_headers(mock_analytics_headers, mock_request):
    _reset_jwt_token_cache()
    client.analytics_request("GET", "/analytics/jobs", json={"query": "foo"})

    mock_request.assert_called_once_with(
        "GET",
        "%s/analytics/jobs" % CONFIG["ANALYTICS_URL"],
        headers=DEFAULT_HEADERS,
        timeout=CONFIG["REQUESTS_TIMEOUT"],
        json={"query": "foo"},
    )


@mock.patch("dci.analytics.client.requests.request")
@mock.patch(
    "dci.analytics.client.analytics_headers", return_value=DEFAULT_HEADERS.copy()
)
def test_analytics_request_merges_kwargs_headers(mock_analytics_headers, mock_request):
    _reset_jwt_token_cache()
    client.analytics_request(
        "GET",
        "/analytics/jobs",
        headers={"X-Custom": "value"},
        json={"query": "foo"},
    )

    expected_headers = DEFAULT_HEADERS.copy()
    expected_headers["X-Custom"] = "value"
    mock_request.assert_called_once_with(
        "GET",
        "%s/analytics/jobs" % CONFIG["ANALYTICS_URL"],
        headers=expected_headers,
        timeout=CONFIG["REQUESTS_TIMEOUT"],
        json={"query": "foo"},
    )


@mock.patch("dci.analytics.client.requests.request")
@mock.patch(
    "dci.analytics.client.analytics_headers", return_value=DEFAULT_HEADERS.copy()
)
def test_analytics_request_auth_headers_not_overwritable(
    mock_analytics_headers, mock_request
):
    _reset_jwt_token_cache()
    client.analytics_request(
        "GET",
        "/analytics/jobs",
        headers={"Authorization": "Bearer evil", "X-Custom": "value"},
    )

    expected_headers = DEFAULT_HEADERS.copy()
    expected_headers["X-Custom"] = "value"
    mock_request.assert_called_once_with(
        "GET",
        "%s/analytics/jobs" % CONFIG["ANALYTICS_URL"],
        headers=expected_headers,
        timeout=CONFIG["REQUESTS_TIMEOUT"],
    )


@mock.patch("dci.analytics.client.requests.request")
@mock.patch(
    "dci.analytics.client.analytics_headers", return_value=DEFAULT_HEADERS.copy()
)
def test_analytics_request_accepts_custom_timeout(mock_analytics_headers, mock_request):
    _reset_jwt_token_cache()
    client.analytics_request("GET", "/analytics/jobs", timeout=42)

    mock_request.assert_called_once_with(
        "GET",
        "%s/analytics/jobs" % CONFIG["ANALYTICS_URL"],
        headers=DEFAULT_HEADERS,
        timeout=42,
    )
