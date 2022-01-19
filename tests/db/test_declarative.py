# -*- encoding: utf-8 -*-
#
# Copyright Red Hat, Inc.
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

from dci.db import declarative as d
import mock


def test_handle_pagination():
    m = mock.MagicMock()
    m.limit = mock.MagicMock()
    m.offset = mock.MagicMock(return_value=m)
    d.handle_pagination(m, {"limit": 20})
    m.offset.assert_called_once_with(0)
    m.limit.assert_called_once_with(20)
    for reset_m in (m, m.limit, m.offset):
        reset_m.reset_mock()
    d.handle_pagination(m, {"limit": 300, "offset": 12})
    m.offset.assert_called_once_with(12)
    m.limit.assert_called_once_with(200)
