# -*- encoding: utf-8 -*-
#
# Copyright 2015-2024 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Global parameters about the API itself
#
import os

HOST = os.getenv("API_HOST", "127.0.0.1")
PORT = int(os.getenv("API_PORT", "5000"))
DEBUG = os.getenv("API_DEBUG", "True").strip().capitalize() == "True"
JSONIFY_PRETTYPRINT_REGULAR = (
    os.getenv("JSONIFY_PRETTYPRINT_REGULAR ", "False").strip().capitalize() == "True"
)

# Database (SQLAlchemy) related parameters
#
DB_USER = os.getenv("DB_USER", "dci")
DB_PASSWORD = os.getenv("DB_PASSWORD", "dci")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "dci")
DEFAULT_SQLALCHEMY_DATABASE_URI = (
    "postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}".format(
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
    )
)
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI", DEFAULT_SQLALCHEMY_DATABASE_URI
)

# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").strip().capitalize() == "True"
SQLALCHEMY_RECORD_QUERIES = (
    os.getenv("SQLALCHEMY_RECORD_QUERIES", "False").strip().capitalize() == "True"
)
SQLALCHEMY_NATIVE_UNICODE = (
    os.getenv("SQLALCHEMY_NATIVE_UNICODE", "True").strip().capitalize() == "True"
)
SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "5"))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "25"))

# Stores configuration, to store files and components
# STORE
SWIFT_STORE = "swift"
S3_STORE = "s3"

STORE_ENGINE = os.getenv("STORE_ENGINE", S3_STORE)

# Generic store
STORE_FILES_CONTAINER = os.getenv("STORE_FILES_CONTAINER", "dci-files")
STORE_COMPONENTS_CONTAINER = os.getenv("STORE_COMPONENTS_CONTAINER", "dci-components")


# S3/minio Store
STORE_S3_AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
STORE_S3_AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
STORE_S3_AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
STORE_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
STORE_S3_SIGNATURE_VERSION = os.getenv("AWS_SIGNATURE_VERSION", "s3v4")

# ZMQ Connection
ZMQ_HOST = os.getenv("ZMQ_HOST", "127.0.0.1")
ZMQ_PORT = int(os.getenv("ZMQ_PORT", "5557"))
DEFAULT_ZMQ_CONN = "tcp://{zmq_host}:{zmq_port}".format(
    zmq_host=ZMQ_HOST, zmq_port=ZMQ_PORT
)
ZMQ_CONN = os.getenv("ZMQ_CONN", DEFAULT_ZMQ_CONN)


# Analytics
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://dci-analytics:2345")


# Logging related parameters
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s"


X_DOMAINS = "*"
X_HEADERS = "Authorization, Content-Type, If-Match, ETag, X-Requested-With, X-DCI-Team-ID"
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "20")) * 1024 * 1024

FILES_UPLOAD_FOLDER = os.getenv(
    "FILES_UPLOAD_FOLDER", "/var/lib/dci-control-server/files"
)

# SSO_PUBLIC_KEY is set by bin/dci-gen-pem-ks-key.py
SSO_PUBLIC_KEY = os.getenv("SSO_PUBLIC_KEY")
SSO_AUDIENCES = os.getenv("SSO_AUDIENCES", "api.dci,dci").split(",")
SSO_READ_ONLY_GROUP = os.getenv("SSO_READ_ONLY_GROUP", "redhat:employees")
SSO_URL = os.getenv("SSO_URL", "https://sso.redhat.com")
SSO_REALM = os.getenv("SSO_REALM", "redhat-external")

CERTIFICATION_URL = os.getenv(
    "CERTIFICATION_URL", "https://access.stage.redhat.com/hydra/rest/cwe/xmlrpc/v2"
)

RHDL_API_URL = os.getenv("RHDL_API_URL", "https://api.rhdl.distributed-ci.io/api/v1")
RHDL_SERVICE_ACCOUNT_ACCESS_KEY = os.getenv("RHDL_SERVICE_ACCOUNT_ACCESS_KEY", "")
RHDL_SERVICE_ACCOUNT_SECRET_KEY = os.getenv("RHDL_SERVICE_ACCOUNT_SECRET_KEY", "")

REQUESTS_TIMEOUT = (
    float(os.getenv("REQUESTS_TIMEOUT_CONNECT", "3.0")),
    float(os.getenv("REQUESTS_TIMEOUT_READ", "10.0")),
)
