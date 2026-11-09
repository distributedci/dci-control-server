import io

import mock

from dci import dci_config


def test_s3_certification_bucket_configuration():
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

    path = "certifications/scans/vulnerabilities/scan/results/result"
    json_path = f"{path}/json"
    csv_path = f"{path}/csv"
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


def test_local_certification_container(tmp_path):
    with mock.patch.dict(
        dci_config.CONFIG,
        {
            "STORE_ENGINE": "filesystem",
            "FILES_UPLOAD_FOLDER": str(tmp_path),
            "STORE_CERTIFICATIONS_CONTAINER": "custom-certifications",
        },
    ):
        dci_config.CONFIG.pop("STORE_FILE_PATH", None)
        store = dci_config.get_store()
    path = "certifications/scans/vulnerabilities/scan/results/result/json"

    store.upload("certifications", path, io.BytesIO(b'[{"cve":"CVE-1"}]'))
    _, stream = store.get("certifications", path)
    with stream:
        assert stream.read() == '[{"cve":"CVE-1"}]'
    assert (tmp_path / "custom-certifications" / path).is_file()
    store.delete("certifications", path)
    assert not (tmp_path / "custom-certifications" / path).exists()


def test_local_storage_path_override(tmp_path):
    with mock.patch.dict(
        dci_config.CONFIG,
        {
            "STORE_ENGINE": "filesystem",
            "FILES_UPLOAD_FOLDER": str(tmp_path / "old"),
            "STORE_FILE_PATH": str(tmp_path / "new"),
        },
    ):
        assert dci_config.get_store().path == str(tmp_path / "new")


def test_local_binary_read_preserves_csv_bytes_and_default_text_mode(tmp_path):
    with mock.patch.dict(
        dci_config.CONFIG,
        {
            "STORE_ENGINE": "filesystem",
            "FILES_UPLOAD_FOLDER": str(tmp_path),
            "STORE_CERTIFICATIONS_CONTAINER": "custom-certifications",
        },
    ):
        dci_config.CONFIG.pop("STORE_FILE_PATH", None)
        store = dci_config.get_store()
    path = "certifications/scans/vulnerabilities/scan/results/result/csv"
    content = b"\xef\xbb\xbfcve\r\nCVE-1\r\nCVE-2"
    store.upload("certifications", path, io.BytesIO(content))

    _, stream = store.get("certifications", path, binary=True)
    with stream:
        assert stream.read() == content
    _, stream = store.get("certifications", path)
    with stream:
        assert stream.read() == "\ufeffcve\nCVE-1\nCVE-2"
