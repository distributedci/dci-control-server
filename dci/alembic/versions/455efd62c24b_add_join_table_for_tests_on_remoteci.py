#
# Copyright (C) 2016 Red Hat, Inc
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

"""add join table for tests on remoteci

Revision ID: 455efd62c24b
Revises: 48c9af8ba5c3
Create Date: 2016-07-29 13:01:01.233131

"""

# revision identifiers, used by Alembic.
revision = '455efd62c24b'
down_revision = '90173a940d2c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'remoteci_tests',
        sa.Column('remoteci_id', sa.String(36),
                  sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('test_id', sa.String(36),
                  sa.ForeignKey('tests.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True)
    )


def downgrade():
    """Not supported at this time, will be implemented later"""
    pass
