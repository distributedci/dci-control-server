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

"""attach components to their product

Revision ID: 151c7129cc09
Revises: 7c1538bc073b
Create Date: 2023-07-21 02:59:38.933407

"""

# revision identifiers, used by Alembic.
revision = "151c7129cc09"
down_revision = "7c1538bc073b"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc
import sys

_topic_to_product = {}


def upgrade():
    s = Session(op.get_bind())
    try:
        s.execute(
            """
INSERT INTO products_components
SELECT topics.product_id, components.id
FROM topics JOIN components ON topics.id = components.topic_id
"""
        )
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
