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

from dci import stores
from dci.common import exceptions

import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3(stores.Store):
    def __init__(self, conf):
        self.aws_access_key_id = conf.get(
            "aws_access_key_id", os.getenv("AWS_ACCESS_KEY_ID")
        )
        self.aws_secret_access_key = conf.get(
            "aws_secret_access_key", os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.aws_region = conf.get("aws_region", os.getenv("AWS_REGION"))

        self.bucket = conf.get("aws_s3_bucket")
        self.s3 = self.get_s3()

    def get_s3(self):
        return boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def delete(self, filename):
        try:
            try:
                self.s3.head_object(Buicket=self.bucket, Key=filename)
            except ClientError as e:
                logger.warn(
                    f"File '{filename}' does not exist or failed to get info: {str(e)}"
                )
                return
            self.s3.delete_object(Bucket=self.bucket, Key=filename)
        except ClientError as e:
            raise exceptions.StoreExceptions(
                f"Error while deleting file '{filename}': {e}"
            )

    def get(self, filename):
        try:
            # self.s3.Client.generate_presigned_url("get_object", Params={'Bucket': self.bucket, "Key": filename}, ExpiresIn=120)
            obj = self.s3.get_object(Bucket=self.bucket, Key=filename)
            return obj, obj["Body"]
        except ClientError as e:
            raise exceptions.StoreException(
                f"Error while getting file '{filename}': {e}"
            )

    def head(self, filename):
        try:
            return self.s3.head_object(Bucket=self.bucket, Key=filename)
        except ClientError as e:
            raise exceptions.StoreException(
                f"Error while heading file '{filename}': {e}"
            )

    def upload(self, file_path, iterable, pseudo_folder=None, create_container=True):
        try:
            self.s3.heat_bucket(Bucket=self.bucket)
        except ClientError:
            if create_container:
                try:
                    self.s3.create_bucket(Bucket=self.bucket)
                except ClientError as exc:
                    raise exceptions.StoreExceptions(
                        f"Error while creating bucket for file '{filename}': {exc}",
                    )

        self.upload_fileobj(iterable, self.bucket, self.file_path)
