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

"""Allow null user email

Revision ID: a5228fbbe93d
Revises: 609db7251b15
Create Date: 2023-08-02 15:49:30.307665

"""

revision = "a5228fbbe93d"
down_revision = "609db7251b15"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        "users", "email", existing_type=sa.String(length=255), nullable=True
    )
    op.drop_constraint("users_email_key", "users", type_="unique")


def downgrade():
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.alter_column(
        "users", "email", existing_type=sa.String(length=255), nullable=False
    )
