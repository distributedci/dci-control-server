#
# Copyright (C) 2022 Red Hat, Inc
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

"""Add display_name and version to Component

Revision ID: 66680dcf2c88
Revises: fd04b7d20477
Create Date: 2022-10-13 12:56:36.347286

"""

# revision identifiers, used by Alembic.
revision = "66680dcf2c88"
down_revision = "fd04b7d20477"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("components", sa.Column("display_name", sa.String(), nullable=True))
    op.add_column("components", sa.Column("version", sa.String(), nullable=True))
    op.drop_constraint("name_topic_id_type_team_id_unique", "components")
    op.create_unique_constraint(
        "name_topic_id_type_team_id_version_unique",
        "components",
        ["name", "topic_id", "type", "team_id", "version"],
    )


def downgrade():
    op.drop_column("components", "version")
    op.drop_column("components", "display_name")
