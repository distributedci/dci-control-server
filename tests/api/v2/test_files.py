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


from dci import dci_config
from dci.stores import files_utils


def test_get_file_content_from_s3(user, job_user_id, app):

    headers = {"DCI-JOB-ID": job_user_id, "DCI-NAME": "name1"}
    pfile = user.post("/api/v1/files", headers=headers, data="kikoolol").data
    file1_id = pfile["file"]["id"]

    # GET
    r = user.get("/api/v2/files/%s/content" % file1_id)
    assert r.status_code == 302
    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_FILES_CONTAINER"]
    file_path = files_utils.build_file_path(
        pfile["file"]["team_id"], pfile["file"]["job_id"], file1_id
    )
    assert r.headers["Location"].startswith(f"{s3_endpoint_url}/{bucket}/{file_path}")

    # HEAD
    r = user.head("/api/v2/files/%s/content" % file1_id)
    assert r.status_code == 302
    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_FILES_CONTAINER"]
    file_path = files_utils.build_file_path(
        pfile["file"]["team_id"], pfile["file"]["job_id"], file1_id
    )
    assert r.headers["Location"].startswith(f"{s3_endpoint_url}/{bucket}/{file_path}")
