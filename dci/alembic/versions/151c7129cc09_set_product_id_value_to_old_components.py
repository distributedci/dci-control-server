#
# Copyright (C) 2023 Red Hat, Inc
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

"""set product_id value to old components

Revision ID: 151c7129cc09
Revises: e02e327dd662
Create Date: 2023-07-21 02:59:38.933407

"""

# revision identifiers, used by Alembic.
revision = "151c7129cc09"
down_revision = "e02e327dd662"
branch_labels = None
depends_on = None

from dci.db import models2
from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc
import sys

_topic_to_product = {}


def upgrade():
    s = Session(op.get_bind())
    try:
        offset = 0
        limit = 1000
        while True:
            query = (
                s.query(models2.Component)
                .filter(models2.Component.state != "archived")
                .offset(offset)
                .limit(limit)
            )
            components = query.all()
            if not components:
                break
            for c in components:
                if c.topic_id not in _topic_to_product:
                    t = (
                        s.query(models2.Topic)
                        .filter(models2.Topic.id == c.topic_id)
                        .one()
                    )
                    _topic_to_product[c.topic_id] = t.product_id
                product_id = _topic_to_product[c.topic_id]
                c.product_id = product_id
                s.add(c)
                s.flush()
            offset += limit
            print(offset)
    except exc.IntegrityError as ie:
        print("rollback" + str(ie))
        s.rollback()
        s.close()
        sys.exit(1)
    except Exception as e:
        print("Exception" + str(e))
        s.rollback()
        s.close()
        sys.exit(1)
    s.commit()


def downgrade():
    pass
