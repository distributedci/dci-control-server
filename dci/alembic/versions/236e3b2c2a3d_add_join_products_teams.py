#
# Copyright (C) 2019 Red Hat, Inc
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

"""add join products teams

Revision ID: 236e3b2c2a3d
Revises: 4e45b2030162
Create Date: 2019-05-31 19:12:57.166953

"""

# revision identifiers, used by Alembic.
revision = '236e3b2c2a3d'
down_revision = '4e45b2030162'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.create_table(
        'products_teams',
        sa.Column('product_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('products.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('team_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('teams.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
    )


def downgrade():
    pass
