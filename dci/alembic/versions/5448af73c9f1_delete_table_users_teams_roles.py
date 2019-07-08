#
# Copyright (C) 2019 Red Hat, Inc
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

"""Delete table users teams roles

Revision ID: 5448af73c9f1
Revises: a46098d949c
Create Date: 2019-07-05 07:13:59.223812

"""

# revision identifiers, used by Alembic.
revision = '5448af73c9f1'
down_revision = 'a46098d949c'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table('users_teams_roles')


def downgrade():
    pass
