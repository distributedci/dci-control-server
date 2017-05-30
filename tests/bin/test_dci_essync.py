# -*- encoding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
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


from dci import dci_config
from dci.elasticsearch import es_client

from tests import utils

conf = dci_config.generate_conf()

es_engine = es_client.DCIESEngine(conf['ES_HOST'], conf['ES_PORT'], 'dci')


def test_essync_add_files(user, jobstate_user_id):
    for i in range(5):
        utils.post_file(user, jobstate_user_id,
                        utils.FileDesc('kikoolol', 'content'))

    env = {'DCI_CS_URL': 'http://127.0.0.1:5000',
           'DCI_LOGIN': 'admin',
           'DCI_PASSWORD': 'admin'}
    status = utils.run_bin('dci-essync', env=env)
    import pprint
    pprint.pprint(status.communicate())
    assert status.returncode == 0
    assert es_engine.get_last_sequence(doc_type='logs') == 5
