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

"""migrate product team components

Revision ID: ab42782464f9
Revises: 151c7129cc09
Create Date: 2023-07-11 22:43:41.661742

"""

# revision identifiers, used by Alembic.
revision = "ab42782464f9"
down_revision = "151c7129cc09"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc, delete
import sys
import uuid

from dci.db.models2 import Component, JOIN_JOBS_COMPONENTS, JOIN_PRODUCTS_COMPONENTS


_topic_to_product = {}


def get_duplicated_components(s):
    """
    This selects the components with:
        - team_id != NULL
        - same display_name, type, version, team_id
    and outputs:
        - one component_id to keep [1]
        - one or more component_ids to be replaced by [1] and then removed

    """
    return s.execute(
        """
SELECT MIN(CAST(c1.id AS VARCHAR)) as KEEP_ID, ARRAY_AGG(c2.id) as REMOVE_IDS
  FROM components as "c1"
  JOIN components as "c2" ON
       c1.display_name = c2.display_name
       AND c1.type = c2.type
       AND c1.version = c2.version
       AND c1.team_id = c2.team_id
       AND c1.id != c2.id
 WHERE c1.team_id IS NOT NULL
 GROUP BY c1.team_id, c1.display_name, c1.type, c1.version
"""
    )


def upgrade():
    session = Session(op.get_bind())
    try:
        duplicated_components = list(get_duplicated_components(session))
        print(len(duplicated_components))
        if duplicated_components:
            # Adding these two indexes boosts searching for the component_id
            op.create_index(
                "tmp_index_jobs_components",
                "jobs_components",
                ["component_id"],
                unique=False,
            )
            op.create_index(
                "tmp_index_products_components",
                "products_components",
                ["component_id"],
                unique=False,
            )
            component_ids_to_remove = []

            for component in duplicated_components:
                # Replace REMOVE_IDS with KEEP_ID in JOIN_JOBS_COMPONENTS
                session.execute(
                    JOIN_JOBS_COMPONENTS.update()
                    .where(
                        JOIN_JOBS_COMPONENTS.c.component_id.in_(component["remove_ids"])
                    )
                    .values(component_id=uuid.UUID(component["keep_id"]))
                )
                component_ids_to_remove.extend(component["remove_ids"])
            # Remove REMOVE_IDS from JOIN_PRODUCTS_COMPONENTS
            session.execute(
                JOIN_PRODUCTS_COMPONENTS.delete().where(
                    JOIN_PRODUCTS_COMPONENTS.c.component_id.in_(component_ids_to_remove)
                )
            )
            # Remove REMOVE_IDS from Components
            session.execute(
                delete(Component).where(Component.id.in_(component_ids_to_remove))
            )

            # Remove the temporary indexes
            op.drop_index("tmp_index_products_components", table_name="jobs_components")
            op.drop_index("tmp_index_jobs_components", table_name="products_components")
    except exc.IntegrityError as ie:
        print("Rollback " + str(ie))
        session.rollback()
        session.close()
        sys.exit(1)
    except Exception as e:
        print("Exception " + str(e))
        session.rollback()
        session.close()
        sys.exit(1)
    session.commit()
    session.close()


def downgrade():
    pass
