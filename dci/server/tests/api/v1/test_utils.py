# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

from dci.server.api.v1 import utils
from dci.server.common import exceptions as dci_exc

import pytest


def test_verify_embed_list():
    valid_embed_list = ['a', 'a.b', 'a.b.c']
    embed_list = ['a', 'a.b.c', 'a.b']
    utils.verify_embed_list(embed_list, valid_embed_list)


def test_verify_embed_list_not_valid():
    valid_embed_list = ['a', 'a.b', 'a.b.c']
    embed_list = ['a', 'a.b', 'kikoolol']

    assert pytest.raises(dci_exc.DCIException,
                         utils.verify_embed_list,
                         embed_list, valid_embed_list)


def test_group_embedded_resources():
    embed_list = ['a', 'b', 'a.c']
    row = {'id': '12', 'name': 'lol',
           'a_id': '123', 'a_name': 'lol2', 'a_c_id': '12345',
           'b_id': '1234', 'b_name': 'lol3',
           'a.c_name': 'mdr1'}
    result = utils.group_embedded_resources(embed_list, row)

    assert {'id': '12', 'name': 'lol',
            'a': {'id': '123', 'name': 'lol2',
                  'c': {'id': '12345', 'name': 'mdr1'}},
            'b': {'id': '1234', 'name': 'lol3'}} == result
