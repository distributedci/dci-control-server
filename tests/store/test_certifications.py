import io

import mock
import pytest

from dci import dci_config
from dci.common import vulnerability_scans
from dci.stores.filesystem import FileSystem


@pytest.mark.parametrize(
    ("certification_id", "encoded_id"),
    [
        ("certification", "certification"),
        ("cert /% é", "cert%20%2F%25%20%C3%A9"),
        (".", "%2E"),
        ("..", "%2E%2E"),
        ("/outside", "%2Foutside"),
    ],
)
def test_s3_certification_bucket_configuration(certification_id, encoded_id):
    client = mock.Mock()
    client.list_buckets.return_value = {
        "Buckets": [
            {"Name": "test-files"},
            {"Name": "test-components"},
        ]
    }

    with mock.patch.dict(
        dci_config.CONFIG,
        {
            "STORE_ENGINE": dci_config.CONFIG["S3_STORE"],
            "STORE_FILES_CONTAINER": "test-files",
            "STORE_COMPONENTS_CONTAINER": "test-components",
            "STORE_CERTIFICATIONS_CONTAINER": "custom-certifications",
        },
    ):
        with mock.patch("dci.stores.s3.S3.get_s3", return_value=client):
            store = dci_config.get_store()

    assert store.containers["certifications"] == "custom-certifications"
    assert "custom-certifications" in store.buckets
    client.create_bucket.assert_called_once_with(Bucket="custom-certifications")

    path = f"certifications/{encoded_id}/scans/vulnerabilities/scan/results/result"
    paths = vulnerability_scans.build_results_paths(certification_id, "scan", "result")
    assert paths == {"json": f"{path}/json", "csv": f"{path}/csv"}
    json_path = paths["json"]
    csv_path = paths["csv"]
    stream = io.BytesIO(b"[]")
    store.upload("certifications", json_path, stream)
    client.head_bucket.assert_called_once_with(Bucket="custom-certifications")
    client.put_object.assert_called_once_with(
        Bucket="custom-certifications", Key=json_path, Body=stream
    )

    client.get_object.return_value = {"Body": io.BytesIO(b"[]")}
    _, result = store.get("certifications", json_path)
    assert result.read() == b"[]"
    client.get_object.assert_called_once_with(
        Bucket="custom-certifications", Key=json_path
    )
    csv_content = b"\xef\xbb\xbfcve\r\nCVE-1\r\n"
    csv_stream = io.BytesIO(csv_content)
    store.upload("certifications", csv_path, csv_stream)
    client.put_object.assert_has_calls(
        [
            mock.call(Bucket="custom-certifications", Key=json_path, Body=stream),
            mock.call(Bucket="custom-certifications", Key=csv_path, Body=csv_stream),
        ]
    )
    client.get_object.return_value = {"Body": io.BytesIO(csv_content)}
    _, result = store.get("certifications", csv_path, binary=True)
    with result:
        assert result.read() == csv_content
    client.get_object.assert_called_with(Bucket="custom-certifications", Key=csv_path)
    store.delete("certifications", json_path)
    store.delete("certifications", csv_path)
    client.delete_object.assert_has_calls(
        [
            mock.call(Bucket="custom-certifications", Key=json_path),
            mock.call(Bucket="custom-certifications", Key=csv_path),
        ]
    )


@pytest.mark.parametrize(
    "certification_id", ["cert /% é", ".", "..", "../outside", "/outside", "//", "%2F"]
)
def test_filesystem_certification_paths_stay_within_container(
    tmp_path, certification_id
):
    store = FileSystem(
        {"path": str(tmp_path), "containers": {"certifications": "bucket"}}
    )
    paths = vulnerability_scans.build_results_paths(certification_id, "scan", "result")
    for result_format, path in paths.items():
        store.upload("certifications", path, io.BytesIO(result_format.encode()))
        stored_file = tmp_path / "bucket" / path
        assert stored_file.resolve().is_relative_to((tmp_path / "bucket").resolve())
        _, stream = store.get("certifications", path, binary=True)
        with stream:
            assert stream.read() == result_format.encode()
        store.delete("certifications", path)
        assert not stored_file.exists()


def test_s3_shared_bucket_is_initialized_once():
    client = mock.Mock()
    client.list_buckets.return_value = {"Buckets": []}

    with mock.patch.dict(
        dci_config.CONFIG,
        {
            "STORE_ENGINE": dci_config.CONFIG["S3_STORE"],
            "STORE_FILES_CONTAINER": "shared",
            "STORE_COMPONENTS_CONTAINER": "shared",
            "STORE_CERTIFICATIONS_CONTAINER": "certs",
        },
    ):
        with mock.patch("dci.stores.s3.S3.get_s3", return_value=client):
            store = dci_config.get_store()

    assert store.buckets == ["shared", "certs"]
    assert client.create_bucket.call_args_list == [
        mock.call(Bucket="shared"),
        mock.call(Bucket="certs"),
    ]
