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

"""add_users_timezone

Revision ID: 014984a4512f
Revises: 5e6c85f69828
Create Date: 2017-07-06 10:20:13.847751

"""

# revision identifiers, used by Alembic.
revision = '014984a4512f'
down_revision = '5e6c85f69828'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users',
                  sa.Column('timezone', sa.String(255),
                            default='UTC', server_default='UTC',
                            nullable=False))


def downgrade():
    pass
