# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

from dci.stores import filesystem, s3

import flask
import sqlalchemy

# this is an application global variable
CONFIG = flask.Config("")
CONFIG.from_object("dci.settings")
CONFIG.from_object(os.environ.get("DCI_SETTINGS_MODULE"))


# todo(yassine): remove the param used by client's CI.
def generate_conf(param=None):
    return CONFIG


def get_engine(db_uri):
    return sqlalchemy.create_engine(
        db_uri,
        pool_size=CONFIG["SQLALCHEMY_POOL_SIZE"],
        max_overflow=CONFIG["SQLALCHEMY_MAX_OVERFLOW"],
        encoding="utf8",
        convert_unicode=CONFIG["SQLALCHEMY_NATIVE_UNICODE"],
        echo=CONFIG["SQLALCHEMY_ECHO"],
    )


def get_store():
    configuration = {
        "containers": {
            "files": CONFIG["STORE_FILES_CONTAINER"],
            "components": CONFIG["STORE_COMPONENTS_CONTAINER"],
        }
    }
    if CONFIG["STORE_ENGINE"] == CONFIG["S3_STORE"]:
        configuration["aws_access_key_id"] = CONFIG["STORE_S3_AWS_ACCESS_KEY_ID"]
        configuration["aws_secret_access_key"] = CONFIG[
            "STORE_S3_AWS_SECRET_ACCESS_KEY"
        ]
        configuration["aws_region"] = CONFIG["STORE_S3_AWS_REGION"]
        configuration["endpoint_url"] = CONFIG.get("STORE_S3_ENDPOINT_URL")
        configuration["signature_version"] = CONFIG.get("STORE_S3_SIGNATURE_VERSION")
        print("config %s" % str(configuration))
        return s3.S3(configuration)
    else:
        configuration["path"] = CONFIG["STORE_FILE_PATH"]
        return filesystem.FileSystem(configuration)
