#
# Copyright (C) 2025 Red Hat, Inc
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

"""add last_auth_at field

Revision ID: 7114805
Revises: 4ff34474b4fd
Create Date: 2025-01-06 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "7114805"
down_revision = "4ff34474b4fd"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("users", sa.Column("last_auth_at", sa.DateTime(), nullable=True))
    op.add_column("remotecis", sa.Column("last_auth_at", sa.DateTime(), nullable=True))
    op.add_column("feeders", sa.Column("last_auth_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("feeders", "last_auth_at")
    op.drop_column("remotecis", "last_auth_at")
    op.drop_column("users", "last_auth_at")
