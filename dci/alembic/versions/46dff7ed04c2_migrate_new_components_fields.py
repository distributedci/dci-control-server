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

"""Migrate new components fields

Revision ID: 46dff7ed04c2
Revises: 66680dcf2c88
Create Date: 2023-01-11 15:37:58.104746

"""

# revision identifiers, used by Alembic.
revision = "46dff7ed04c2"
down_revision = "66680dcf2c88"
branch_labels = None
depends_on = None

from dci.api.v1.components import get_component_display_name, get_component_version
from dci.db import models2

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc


def upgrade():
    session = Session(op.get_bind())

    limit = 100
    query = (
        session.query(models2.Component)
        .order_by(models2.Component.created_at.asc())
        .limit(limit)
    )

    offset = 0
    try:
        while True:
            query = query.offset(offset)

            components = query.all()
            if not components:
                break
            for c in components:
                name = c.canonical_project_name or c.name
                if not c.display_name:
                    c.display_name = get_component_display_name(name)
                if not c.version:
                    c.version = get_component_version(name)
                c.title = c.title or ""
                c.message = c.message or ""
                c.canonical_project_name = c.canonical_project_name or ""

            offset += limit
    except exc.IntegrityError:
        session.rollback()
        session.close()
    except Exception:
        session.rollback()
        session.close()

    session.commit()
    session.close()


def downgrade():
    pass
