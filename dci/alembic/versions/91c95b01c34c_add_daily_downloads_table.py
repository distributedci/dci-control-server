#
# Copyright (C) 2024 Red Hat, Inc
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

"""Add daily_downloads table

Revision ID: 91c95b01c34c
Revises: 83c6c24dc160
Create Date: 2024-06-04 12:35:13.801266

"""

# revision identifiers, used by Alembic.
revision = "91c95b01c34c"
down_revision = "83c6c24dc160"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "daily_downloads",
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("total_downloaded", sa.BIGINT(), nullable=False),
        sa.ForeignKeyConstraint(
            ["component_id"], ["components.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "component_id", "day"),
    )
    op.create_index(
        "daily_downloads_pk",
        "daily_downloads",
        ["team_id", "component_id", "day"],
        unique=True,
    )


def downgrade():
    op.drop_index("daily_downloads_pk", table_name="daily_downloads")
    op.drop_table("daily_downloads")
