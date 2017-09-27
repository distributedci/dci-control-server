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

"""Make team_id,password nullable

Revision ID: 6f875bc66ca9
Revises: beb07deee8e6
Create Date: 2017-09-22 18:50:30.205189

"""

# revision identifiers, used by Alembic.
revision = '6f875bc66ca9'
down_revision = 'beb07deee8e6'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.alter_column('users', 'team_id', nullable=True)
    op.alter_column('users', 'password', nullable=True)


def downgrade():
    pass
