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

"""add tasks

Revision ID: d7bd828625ee
Revises: 7114805
Create Date: 2025-12-17 09:23:53.764714

"""

# revision identifiers, used by Alembic.
revision = "d7bd828625ee"
down_revision = "7114805"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("etag", sa.String(length=40), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("completed", "failed", "skipped", "ignored", name="task_statuses"),
            nullable=False,
        ),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("active", "inactive", "archived", name="states"),
            nullable=False,
        ),
        sa.Column("jobstate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["jobstate_id"], ["jobstates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("tasks_jobstate_id_idx", "tasks", ["jobstate_id"], unique=False)


def downgrade():
    op.drop_index("tasks_jobstate_id_idx", table_name="tasks")
    op.drop_table("tasks")
