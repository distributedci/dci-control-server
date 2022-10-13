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

from dci import dci_config
from dci.db import models2

from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc


def upgrade():
    sqlalchemy_db_uri = dci_config.generate_conf()["SQLALCHEMY_DATABASE_URI"]
    engine = dci_config.get_engine(sqlalchemy_db_uri)
    session = sessionmaker(bind=engine)()

    query = session.query(models2.Component)
    offset = 0
    limit = 100

    while True:
        try:
            query = query.offset(offset)
            query = query.limit(limit)
            components = query.all()
            if not components:
                break
            for c in components:
                if c.display_name and c.version:
                    continue
                c.display_name = c.canonical_project_name
                if " " in c.canonical_project_name:
                    c.display_name = c.canonical_project_name.split(" ")[0]
                c.version = c.name
                if " " in c.name:
                    c.version = c.name.split(" ")[1]
        except exc.IntegrityError as ie:
            session.rollback()
            break
        except Exception as e:
            session.rollback()
            break
        offset += limit


def downgrade():
    pass
