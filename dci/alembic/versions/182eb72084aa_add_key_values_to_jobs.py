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

"""Add key_values to jobs

Revision ID: 182eb72084aa
Revises: fd04b7d20477
Create Date: 2023-01-31 11:21:21.301877

"""

# revision identifiers, used by Alembic.
revision = "182eb72084aa"
down_revision = "fd04b7d20477"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy_utils as sa_utils


def upgrade():
    op.add_column("jobs", sa.Column("keys_values", sa_utils.JSONType, default={}))


def downgrade():
    pass
