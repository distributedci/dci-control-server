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

from dci.db.migration_components import get_new_component_info
from dci.db import models2

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc
import sqlalchemy as sa
import sys


def upgrade():
    session = Session(op.get_bind())

    # this dict will be used to remove redundancy for the creation of the indexes
    occurrences_components = {}
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
                if not c.display_name or not c.version:
                    component_info = get_new_component_info(
                        {
                            "name": c.name,
                            "canonical_project_name": c.canonical_project_name,
                        }
                    )
                    c.display_name = component_info["display_name"]
                    c.version = component_info["version"]
                    c.uid = component_info["uid"]
                c.title = c.title or ""
                c.message = c.message or ""
                c.canonical_project_name = c.canonical_project_name or ""
                _key = "%s-%s-%s-%s-%s" % (
                    c.display_name,
                    c.topic_id,
                    c.type,
                    c.version,
                    c.team_id,
                )
                if _key not in occurrences_components:
                    occurrences_components[_key] = [c]
                else:
                    occurrences_components[_key].append(c)
            offset += limit
    except exc.IntegrityError:
        session.rollback()
        session.close()
        sys.exit(0)
    except Exception:
        session.rollback()
        session.close()
        sys.exit(0)
    session.commit()
    session.close()

    session = Session(op.get_bind())
    for v in occurrences_components.values():
        # keep the latest
        for c in v[:-1]:
            print("delete component %s" % c.display_name)
            session.delete(c)

    op.create_index(
        "active_display_name_topic_id_type_version_team_id_not_null_key",
        "components",
        ["display_name", "topic_id", "type", "version", "team_id"],
        unique=True,
        postgresql_where=sa.text(
            "components.state = 'active' AND components.team_id is not NULL"
        ),
    )

    op.create_index(
        "active_display_name_topic_id_type_version_team_id_null_key",
        "components",
        ["display_name", "topic_id", "type", "version"],
        unique=True,
        postgresql_where=sa.text(
            "components.state = 'active' AND components.team_id is NULL"
        ),
    )


def downgrade():
    pass
