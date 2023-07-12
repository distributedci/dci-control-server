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
Revises: e02e327dd662
Create Date: 2023-07-11 22:43:41.661742

"""

# revision identifiers, used by Alembic.
revision = 'ab42782464f9'
down_revision = 'e02e327dd662'
branch_labels = None
depends_on = None

from dci.db import models2

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc
import sys
import uuid


_topic_to_product = {}


def get_components_teams(s):
    query = s.query(models2.Component).filter(models2.Component.team_id != None).filter(models2.Component.state != "archived")
    return query.all()


def create_product_team_component(s, c):
    topic_id = c.topic_id
    if topic_id not in _topic_to_product:
        t = s.query(models2.Topic).filter(models2.Topic.id == topic_id).one()
        _topic_to_product[topic_id] = t.product_id

    product_team_component = models2.Component(id=uuid.uuid4(),
                                               released_at=c.released_at,
                                               name=c.name,
                                               type=c.type,
                                               canonical_project_name=c.canonical_project_name,
                                               display_name=c.display_name,
                                               version=c.version,
                                               uid=c.uid,
                                               data=c.data,
                                               title=c.title,
                                               message=c.message,
                                               url=c.url,
                                               product_id=_topic_to_product[topic_id],
                                               team_id=c.team_id,
                                               state="active",
                                               tags=c.tags,
                                               files=c.files,
                                               jobs=c.jobs)
    s.add(product_team_component)
    return product_team_component


def upgrade():
    session = Session(op.get_bind())
    try:
        components_teams = get_components_teams(session)
        components_teams_uniq_groups = {}
        components_to_delete = []
        for ct in components_teams:
            k = "%s/%s/%s/%s/%s" % (ct.display_name, ct.topic_id, ct.type, ct.version, ct.team_id)
            if k not in components_teams_uniq_groups:
                components_teams_uniq_groups[k] = create_product_team_component(session, ct)
            for j in ct.jobs:
                j.components.remove(ct)
                if components_teams_uniq_groups[k] not in j.components:
                    j.components.append(components_teams_uniq_groups[k])
                session.add(j)
                session.flush()
            components_to_delete.append(ct)
    
        for ctd in components_to_delete:
            session.delete(ctd)

    except exc.IntegrityError as ie:
        print("rollback" + str(ie))
        session.rollback()
        session.close()
        sys.exit(1)
    except Exception as e:
        print("Exception" + str(e))
        session.rollback()
        session.close()
        sys.exit(1)
    session.commit()


def downgrade():
    pass
