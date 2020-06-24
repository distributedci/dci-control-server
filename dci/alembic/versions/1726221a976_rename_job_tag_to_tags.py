#
# Copyright (C) 2020 Red Hat, Inc
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

"""rename job tag to tags

Revision ID: 1726221a976
Revises: 45e44e338043
Create Date: 2020-06-04 11:39:05.781420

"""

# revision identifiers, used by Alembic.
revision = '1726221a976'
down_revision = '45e44e338043'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.alter_column('jobs', 'tag', new_column_name='tags')


def downgrade():
    pass
