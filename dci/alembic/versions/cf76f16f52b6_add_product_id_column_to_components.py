#
# Copyright (C) 2021 Red Hat, Inc
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

"""add product_id column to components

Revision ID: cf76f16f52b6
Revises: 61f71f157057
Create Date: 2021-12-15 15:40:08.679191

"""

# revision identifiers, used by Alembic.
revision = 'cf76f16f52b6'
down_revision = '61f71f157057'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column('components', sa.Column('product_id', pg.UUID(as_uuid=True),
                                          sa.ForeignKey('products.id', ondelete='CASCADE'),
                                          nullable=True))

    op.drop_constraint(constraint_name='name_topic_id_type_team_id_unique', table_name='components')
    op.create_unique_constraint(name='components_name_product_id_topic_id_key',
                                table_name='components',
                                columns=['name', 'product_id', 'topic_id', 'type', 'team_id'])


def downgrade():
    pass
