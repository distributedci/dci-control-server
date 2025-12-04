# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

import secrets


def gen_secret(length=64, prefix="DCI."):
    """
    Generates a secret using python's 'secrets' module.
    The secret starts with a stable prefix followed by high-entropy hex data.

    Args:
        length (int): total length of the final secret (including prefix)
        prefix (str): stable token prefix used for detection

    Returns:
        str: generated secret
    """
    if length <= len(prefix):
        raise ValueError("Length must be greater than the prefix length")

    nbytes = (length - len(prefix)) // 2
    body = secrets.token_hex(nbytes)

    secret = prefix + body

    missing_length = length - len(secret)
    if missing_length > 0:
        extra = secrets.token_hex(missing_length)[:missing_length]
        secret += extra

    return secret
