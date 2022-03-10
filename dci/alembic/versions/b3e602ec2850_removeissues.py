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

"""RemoveIssues

Revision ID: b3e602ec2850
Revises: 980e18983453
Create Date: 2022-03-10 08:43:03.993092

"""

# revision identifiers, used by Alembic.
revision = "b3e602ec2850"
down_revision = "980e18983453"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table("components_issues")
    op.drop_table("jobs_issues")
    op.drop_table("issues_tests")
    op.drop_table("issues")


def downgrade():
    pass
