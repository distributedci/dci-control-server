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

from dci.api.v1 import utils as v1_utils
from dci.db import models


def check(user, topic):
    """ If the topic has it's export_control set to True then all the teams
    under the product team can access to the topic's resources.

    :param user:
    :param topic:
    :return: True if check is ok, False otherwise
    """
    # if export_control then check the team is associated to the product
    # this will actually check that the root team is the same as the main
    # product team
    if topic['export_control']:
        product = v1_utils.verify_existence_and_get(topic['product_id'],
                                                    models.PRODUCTS)
        return user.product_team_id == product['team_id']
