import flask
import mock
import pytest
from dciauth.v2.headers import parse_headers
from dciauth.v2.signature import is_valid

from tests import utils as test_utils

REMOTECI = {
    "id": "test-remoteci",
    "api_secret": "test-secret",
    "type": "remoteci",
}


@pytest.fixture
def hmac_test_client():
    app = flask.Flask(__name__)

    @app.route("/capture", methods=["GET", "POST"])
    def capture_request():
        content = flask.request.get_data()
        valid, error = is_valid(
            {
                "method": flask.request.method,
                "endpoint": flask.request.path,
                "params": flask.request.args.to_dict(flat=True),
                "data": content,
            },
            {"secret_key": REMOTECI["api_secret"]},
            parse_headers(flask.request.headers),
        )
        return flask.jsonify(
            body=content.hex(),
            content_type=flask.request.content_type,
            valid=valid,
            error=error,
        )

    return test_utils.generate_token_based_client(app, REMOTECI)


@pytest.mark.parametrize(
    "payload",
    [
        b"cve,severity\r\nCVE-1,High\r\n",
        b"",
        b"\xef\xbb\xbfcve\nCVE-1\n",
        "cve\nCVE-é\n".encode("utf-8"),
        b"cve\n\xff\xfe\n",
    ],
    ids=["csv", "empty", "bom", "utf8", "invalid-utf8"],
)
@pytest.mark.parametrize(
    ("header_name", "content_type"),
    [
        (None, "text/csv"),
        (None, "text/csv; charset=utf-8"),
        ("Content-Type", "text/csv"),
        ("content-type", "text/csv; charset=utf-8"),
        ("Content-Type", "application/octet-stream"),
    ],
    ids=["argument", "argument-charset", "header", "lowercase-header", "binary"],
)
def test_hmac_client_sends_and_signs_raw_bytes(
    hmac_test_client, payload, header_name, content_type
):
    options = (
        {"headers": {header_name: content_type}}
        if header_name
        else {"content_type": content_type}
    )
    with mock.patch.object(
        test_utils, "generate_headers", wraps=test_utils.generate_headers
    ) as signer:
        response = hmac_test_client.post(
            "/capture?limit=10&search=some+value", data=payload, **options
        )

    assert response.status_code == 200
    assert response.data == {
        "body": payload.hex(),
        "content_type": content_type,
        "valid": True,
        "error": "",
    }
    assert signer.call_count == 1
    assert signer.call_args.args[0]["data"] == payload


@pytest.mark.parametrize(
    ("payload", "encoded"),
    [
        (
            {"cve": "CVE-é", "severity": "High"},
            b'{"cve": "CVE-\\u00e9", "severity": "High"}',
        ),
        (["CVE-1", "CVE-2"], b'["CVE-1", "CVE-2"]'),
        ("value", b'"value"'),
        ({}, b""),
        (None, b""),
    ],
)
def test_hmac_client_keeps_json_behavior(hmac_test_client, payload, encoded):
    response = hmac_test_client.post(
        "/capture", data=payload, headers={"Content-Type": "text/plain"}
    )

    assert response.status_code == 200
    assert response.data == {
        "body": encoded.hex(),
        "content_type": "application/json",
        "valid": True,
        "error": "",
    }


def test_hmac_client_uses_json_content_type_by_default(hmac_test_client):
    response = hmac_test_client.post("/capture", data=b"csv\n")

    assert response.status_code == 200
    assert response.data == {
        "body": b"csv\n".hex(),
        "content_type": "application/json",
        "valid": True,
        "error": "",
    }


def test_hmac_client_signs_an_empty_get(hmac_test_client):
    response = hmac_test_client.get("/capture?limit=2&offset=1")

    assert response.status_code == 200
    assert response.data == {
        "body": "",
        "content_type": "application/json",
        "valid": True,
        "error": "",
    }


def test_hmac_client_rejects_signature_of_a_different_body(hmac_test_client):
    generate_headers = test_utils.generate_headers
    payload = b"cve\nCVE-1\n"

    def sign_other_content(request, credentials):
        return generate_headers({**request, "data": b"other"}, credentials)

    with mock.patch.object(
        test_utils, "generate_headers", side_effect=sign_other_content
    ) as signer:
        response = hmac_test_client.post(
            "/capture", data=payload, content_type="text/csv"
        )

    assert response.status_code == 200
    assert response.data == {
        "body": payload.hex(),
        "content_type": "text/csv",
        "valid": False,
        "error": "signature is invalid",
    }
    assert signer.call_count == 1
    assert signer.call_args.args[0]["data"] == payload
