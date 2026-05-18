# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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
from dci.common import signature
from dci.common import utils
from dci.common import time
from dci.db import declarative as dci_declarative

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import orm as sa_orm
import sqlalchemy_utils as sa_utils


class Base(DeclarativeBase):
    pass


JOB_STATUSES = [
    "new",
    "pre-run",
    "running",
    "post-run",
    "success",
    "failure",
    "killed",
    "error",
]
STATUSES = sa.Enum(*JOB_STATUSES, name="statuses")
FINAL_STATUSES = ["success", "failure", "error"]
FINAL_FAILURE_STATUSES = ["failure", "error"]
FINAL_STATUSES_ENUM = sa.Enum(*FINAL_STATUSES, name="final_statuses")

RESOURCE_STATES = ["active", "inactive", "archived"]
STATES = sa.Enum(*RESOURCE_STATES, name="states")

ISSUE_TRACKERS = ["github", "bugzilla"]
TRACKERS = sa.Enum(*ISSUE_TRACKERS, name="trackers")


USERS_TEAMS = sa.Table(
    "users_teams",
    Base.metadata,
    sa.Column(
        "user_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "team_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
    ),
    sa.UniqueConstraint("user_id", "team_id", name="users_teams_key"),
)

USER_REMOTECIS = sa.Table(
    "user_remotecis",
    Base.metadata,
    sa.Column(
        "user_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "remoteci_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("remotecis.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


class User(dci_declarative.Mixin, Base):
    __tablename__ = "users"

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column(sa.String(255), nullable=False, unique=True)
    sso_username = sa.Column(sa.String(255), nullable=True, unique=True)
    sso_sub = sa.Column(sa.String(255), nullable=True, unique=True)
    fullname = sa.Column(sa.String(255), nullable=False)
    email = sa.Column(sa.String(255), nullable=True, unique=True)
    password = sa.Column(sa.Text, nullable=True)
    timezone = sa.Column(sa.String(255), nullable=False, default="UTC")
    state = sa.Column(STATES, default="active")
    last_auth_at = sa.Column(sa.DateTime(), nullable=True)
    team = sa_orm.relationship("Team", secondary=USERS_TEAMS, back_populates="users")
    remotecis = sa_orm.relationship(
        "Remoteci", secondary=USER_REMOTECIS, back_populates="users"
    )


User.api_fields = list(n for n in User.__mapper__.columns.keys() if n != "password")


JOIN_PRODUCTS_TEAMS = sa.Table(
    "products_teams",
    Base.metadata,
    sa.Column(
        "product_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "team_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


JOIN_TEAMS_COMPONENTS_ACCESS = sa.Table(
    "teams_components_access",
    Base.metadata,
    sa.Column(
        "team_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "access_team_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


class Team(dci_declarative.Mixin, Base):
    __tablename__ = "teams"
    __table_args__ = (sa.UniqueConstraint("name", name="teams_name_key"),)

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column(sa.String(255), nullable=False)
    # https://en.wikipedia.org/wiki/ISO_3166-1 Alpha-2 code
    country = sa.Column(sa.String(255), nullable=True)
    state = sa.Column(STATES, default="active")
    external = sa.Column(sa.BOOLEAN, default=True)
    has_pre_release_access = sa.Column(
        sa.BOOLEAN, nullable=False, default=False, server_default="false"
    )
    users = sa_orm.relationship("User", secondary=USERS_TEAMS, back_populates="team")
    remotecis = sa_orm.relationship("Remoteci", back_populates="team")
    feeders = sa_orm.relationship("Feeder", back_populates="team")
    products = sa_orm.relationship(
        "Product", secondary=JOIN_PRODUCTS_TEAMS, back_populates="teams"
    )
    components_access_teams = sa_orm.relationship(
        "Team",
        secondary=JOIN_TEAMS_COMPONENTS_ACCESS,
        primaryjoin=id == JOIN_TEAMS_COMPONENTS_ACCESS.c.team_id,
        secondaryjoin=id == JOIN_TEAMS_COMPONENTS_ACCESS.c.access_team_id,
    )


Team.api_fields = list(Team.__mapper__.columns.keys())


class UserTopic(dci_declarative.Mixin, Base):
    __tablename__ = "users_topics"
    user_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    topic_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )


UserTopic.api_fields = list(UserTopic.__mapper__.columns.keys())


class Topic(dci_declarative.Mixin, Base):
    __tablename__ = "topics"
    __table_args__ = (
        sa.Index("topics_product_id_idx", "product_id"),
        sa.Index("topics_next_topic_id_idx", "next_topic_id"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column(sa.String(255), unique=True, nullable=False)
    component_types = sa.Column(pg.JSON, default=[])
    component_types_optional = sa.Column(pg.JSON, default=[])
    product_id = sa.Column(
        pg.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True
    )
    next_topic_id = sa.Column(
        pg.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=True, default=None
    )
    export_control = sa.Column(
        sa.BOOLEAN, nullable=False, default=False, server_default="false"
    )
    state = sa.Column(STATES, default="active")
    data = sa.Column(sa_utils.JSONType, default={})
    product = sa_orm.relationship("Product", back_populates="topics")
    next_topic = sa_orm.relationship("Topic", remote_side="Topic.id")


Topic.api_fields = list(Topic.__mapper__.columns.keys())
Topic.api_fields_without_data = list(n for n in Topic.api_fields if n != "data")


class Remoteci(dci_declarative.Mixin, Base):
    __tablename__ = "remotecis"
    __table_args__ = (
        sa.Index("remotecis_team_id_idx", "team_id"),
        sa.UniqueConstraint("name", "team_id", name="remotecis_name_team_id_key"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column("name", sa.String(255))
    data = sa.Column("data", sa_utils.JSONType, default={})
    api_secret = sa.Column("api_secret", sa.String(64), default=signature.gen_secret)
    team_id = sa.Column(
        "team_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    public = sa.Column("public", sa.BOOLEAN, default=False)
    state = sa.Column("state", STATES, default="active")
    last_auth_at = sa.Column(sa.DateTime(), nullable=True)
    users = sa_orm.relationship(
        "User", secondary=USER_REMOTECIS, back_populates="remotecis"
    )
    team = sa_orm.relationship("Team", back_populates="remotecis")


Remoteci.api_fields = list(Remoteci.__mapper__.columns.keys())
Remoteci.api_fields_without_api_secret = list(
    n for n in Remoteci.api_fields if n != "api_secret"
)


class Product(dci_declarative.Mixin, Base):
    __tablename__ = "products"

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column("name", sa.String(255), nullable=False)
    label = sa.Column("label", sa.String(255), nullable=False, unique=True)
    description = sa.Column("description", sa.Text)
    state = sa.Column("state", STATES, default="active")
    topics = sa_orm.relationship("Topic")
    teams = sa_orm.relationship(
        "Team", secondary=JOIN_PRODUCTS_TEAMS, back_populates="products"
    )


Product.api_fields = list(Product.__mapper__.columns.keys())


class Feeder(dci_declarative.Mixin, Base):
    __tablename__ = "feeders"
    __table_args__ = (
        sa.Index("feeders_team_id_idx", "team_id"),
        sa.UniqueConstraint("name", "team_id", name="feeders_name_team_id_key"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column("name", sa.String(255), nullable=False)
    data = sa.Column("data", sa_utils.JSONType, default={})
    api_secret = sa.Column("api_secret", sa.String(64), default=signature.gen_secret)
    team_id = sa.Column(
        "team_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    state = sa.Column("state", STATES, default="active")
    last_auth_at = sa.Column(sa.DateTime(), nullable=True)
    team = sa_orm.relationship("Team", back_populates="feeders")


Feeder.api_fields = list(Feeder.__mapper__.columns.keys())
Feeder.api_fields_without_api_secret = list(
    n for n in Feeder.api_fields if n != "api_secret"
)


class Log(Base):
    __tablename__ = "logs"
    __table_args__ = (sa.Index("logs_user_id_idx", "user_id"),)
    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    user_id = sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False)
    action = sa.Column(sa.Text, nullable=False)


Log.api_fields = list(Log.__mapper__.columns.keys())


JOIN_JOBS_COMPONENTS = sa.Table(
    "jobs_components",
    Base.metadata,
    sa.Column(
        "job_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "component_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


class Componentfile(dci_declarative.Mixin, Base):
    __tablename__ = "component_files"
    __table_args__ = (sa.Index("component_files_component_id_idx", "component_id"),)

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column(sa.String(255), nullable=False)
    mime = sa.Column(sa.String)
    md5 = sa.Column(sa.String(32))
    size = sa.Column(sa.BIGINT, nullable=True)
    component_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("components.id", ondelete="CASCADE"),
        nullable=True,
    )
    state = sa.Column(STATES, default="active")


Componentfile.api_fields = list(Componentfile.__mapper__.columns.keys())


class Component(dci_declarative.Mixin, Base):
    __tablename__ = "components"
    __table_args__ = (
        sa.Index(
            "active_display_name_topic_id_type_version_team_id_null_key",
            "display_name",
            "topic_id",
            "type",
            "version",
            unique=True,
            postgresql_where=sa.sql.text(
                "components.state = 'active' AND components.team_id is NULL"
            ),
        ),
        sa.Index(
            "active_display_name_topic_id_type_version_team_id_not_null_key",
            "display_name",
            "topic_id",
            "type",
            "version",
            "team_id",
            unique=True,
            postgresql_where=sa.sql.text(
                "components.state = 'active' AND components.team_id is not NULL"
            ),
        ),
        sa.Index("components_topic_id_idx", "topic_id"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    released_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    type = sa.Column(sa.String(255), nullable=False)
    canonical_project_name = sa.Column(sa.String)
    display_name = sa.Column(sa.String, nullable=False, server_default="")
    version = sa.Column(sa.String, nullable=False, server_default="")
    uid = sa.Column(sa.String, nullable=False, server_default="")
    data = sa.Column(sa_utils.JSONType)
    title = sa.Column(sa.Text)
    message = sa.Column(sa.Text)
    url = sa.Column(sa.Text)
    topic_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=True,
    )
    team_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
    )
    state = sa.Column(STATES, default="active")
    tags = sa.Column(pg.ARRAY(sa.Text), default=[])
    files = sa_orm.relationship("Componentfile")
    jobs = sa_orm.relationship(
        "Job", secondary=JOIN_JOBS_COMPONENTS, back_populates="components"
    )
    topic = sa_orm.relationship("Topic")


Component.api_fields = list(Component.__mapper__.columns.keys())
Component.api_fields_without_data = list(n for n in Component.api_fields if n != "data")


class Job(dci_declarative.Mixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        sa.Index("jobs_topic_id_idx", "topic_id"),
        sa.Index("jobs_remoteci_id_idx", "remoteci_id"),
        sa.Index("jobs_team_id_idx", "team_id"),
        sa.Index("jobs_product_id_idx", "product_id"),
        sa.Index("jobs_previous_job_id_idx", "previous_job_id"),
        sa.Index("jobs_update_previous_job_id_idx", "update_previous_job_id"),
        sa.Index("jobs_created_at_idx", "created_at"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    # duration in seconds
    duration = sa.Column(sa.Integer, default=0)
    comment = sa.Column(sa.Text, nullable=False, default="")
    status_reason = sa.Column(sa.Text, nullable=False, default="")
    configuration = sa.Column(sa.Text, nullable=False, default="")
    url = sa.Column(sa.Text, nullable=False, default="")
    name = sa.Column(sa.Text, nullable=False, default="")
    status = sa.Column(STATUSES, default="new")
    topic_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("topics.id", ondelete="CASCADE"),
        # todo(yassine): nullable=False
        nullable=True,
    )
    remoteci_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("remotecis.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
    )
    pipeline_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_agent = sa.Column(sa.String(255), nullable=False, default="")
    client_version = sa.Column(sa.String(255), nullable=False, default="")
    previous_job_id = sa.Column(
        pg.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True, default=None
    )
    update_previous_job_id = sa.Column(
        pg.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True, default=None
    )
    state = sa.Column(STATES, default="active")
    tags = sa.Column(pg.ARRAY(sa.Text), default=[])
    data = sa.Column(sa_utils.JSONType, default={})
    components = sa_orm.relationship(
        "Component", secondary=JOIN_JOBS_COMPONENTS, back_populates="jobs"
    )
    results = sa_orm.relationship("TestsResult")
    remoteci = sa_orm.relationship("Remoteci")
    topic = sa_orm.relationship("Topic")
    product = sa_orm.relationship("Product")
    team = sa_orm.relationship("Team")
    jobstates = sa_orm.relationship("Jobstate", order_by="Jobstate.created_at.asc()")
    files = sa_orm.relationship(
        "File", primaryjoin="and_(File.job_id == Job.id, File.jobstate_id == None)"
    )
    pipeline = sa_orm.relationship("Pipeline")
    keys_values = sa_orm.relationship("JobKeyValue")


Job.api_fields = list(Job.__mapper__.columns.keys())
Job.api_fields_without_data = list(n for n in Job.api_fields if n != "data")


class JobKeyValue(dci_declarative.Mixin, Base):
    __tablename__ = "jobs_keys_values"
    __table_args__ = (
        sa.Index("jobs_keys_values_key_idx", "key"),
        sa.Index("jobs_keys_values_job_id_idx", "job_id"),
    )
    job_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    key = sa.Column(sa.String(255), nullable=False, primary_key=True)
    value = sa.Column(sa.Float(), nullable=False)


JobKeyValue.api_fields = list(JobKeyValue.__mapper__.columns.keys())


class Jobstate(dci_declarative.Mixin, Base):
    __tablename__ = "jobstates"
    __table_args__ = (sa.Index("jobstates_job_id_idx", "job_id"),)

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    status = sa.Column(STATUSES, nullable=False)
    comment = sa.Column(sa.Text)
    job_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    files = sa_orm.relationship("File")


Jobstate.api_fields = list(Jobstate.__mapper__.columns.keys())


class TestsResult(dci_declarative.Mixin, Base):
    __tablename__ = "tests_results"
    __table_args__ = (
        sa.Index("tests_results_job_id_idx", "job_id"),
        sa.Index("tests_results_file_id_idx", "file_id"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    name = sa.Column(sa.String(255), nullable=False)
    total = sa.Column(sa.Integer)
    success = sa.Column(sa.Integer)
    skips = sa.Column(sa.Integer)
    failures = sa.Column(sa.Integer)
    regressions = sa.Column(sa.Integer, default=0)
    successfixes = sa.Column(sa.Integer, default=0)
    errors = sa.Column(sa.Integer)
    time = sa.Column(sa.Integer)
    job_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
    )


TestsResult.api_fields = list(TestsResult.__mapper__.columns.keys())


class File(dci_declarative.Mixin, Base):
    __tablename__ = "files"
    __table_args__ = (
        sa.Index("files_jobstate_id_idx", "jobstate_id"),
        sa.Index("files_team_id_idx", "team_id"),
        sa.Index("files_job_id_idx", "job_id"),
    )

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column(sa.String(255), nullable=False)
    mime = sa.Column(sa.String)
    md5 = sa.Column(sa.String(32))
    size = sa.Column(sa.BIGINT, nullable=True)
    state = sa.Column(STATES, default="active")
    jobstate_id = sa.Column(
        "jobstate_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobstates.id", ondelete="CASCADE"),
        nullable=True,
    )
    team_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=True,
    )


File.api_fields = list(File.__mapper__.columns.keys())


class JobEvent(dci_declarative.Mixin, Base):
    __tablename__ = "jobs_events"
    __table_args__ = (sa.Index("jobs_events_job_id_idx", "job_id"),)
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    job_id = sa.Column("job_id", pg.UUID(as_uuid=True), nullable=False)
    topic_id = sa.Column("topic_id", pg.UUID(as_uuid=True), nullable=False)
    status = sa.Column("status", FINAL_STATUSES_ENUM)


JobEvent.api_fields = list(JobEvent.__mapper__.columns.keys())


class Counter(dci_declarative.Mixin, Base):
    __tablename__ = "counter"
    name = sa.Column(sa.String(255), primary_key=True, nullable=False)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    sequence = sa.Column(sa.Integer, default=0)
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )


Counter.api_fields = list(Counter.__mapper__.columns.keys())


class Pipeline(dci_declarative.Mixin, Base):
    __tablename__ = "pipelines"

    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(), default=time.get_utc_now, nullable=False)
    updated_at = sa.Column(
        sa.DateTime(),
        onupdate=time.get_utc_now,
        default=time.get_utc_now,
        nullable=False,
    )
    etag = sa.Column(
        sa.String(40), nullable=False, default=utils.gen_etag, onupdate=utils.gen_etag
    )
    name = sa.Column(sa.String(255), nullable=False)
    team_id = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    team = sa_orm.relationship("Team")
    state = sa.Column(STATES, default="active")


Pipeline.api_fields = list(Pipeline.__mapper__.columns.keys())


# we declare all the relashionships at the end of the file to avoid circular references
_job_relationships = [
    {"results": TestsResult.api_fields},
    {"components": Component.api_fields},
    {"topic": Topic.api_fields_without_data},
    {"team": Team.api_fields},
    {"pipeline": Pipeline.api_fields},
    {"keys_values": JobKeyValue.api_fields},
    {"files": File.api_fields},
    {"jobstates": Jobstate.api_fields},
    {"remoteci": Remoteci.api_fields_without_api_secret},
    {"product": Product.api_fields},
]
Job.api_fields.extend(_job_relationships)
Job.api_fields_without_data.extend(_job_relationships)


Team.api_fields.extend(
    [
        {"remotecis": Remoteci.api_fields_without_api_secret},
        {"feeders": Feeder.api_fields_without_api_secret},
        {"products": Product.api_fields},
        {"components_access_teams": Team.api_fields},
        {"users": User.api_fields},
    ]
)


Jobstate.api_fields.extend(
    [
        {"files": File.api_fields},
    ]
)


User.api_fields.extend(
    [
        {"team": Team.api_fields},
        {"remotecis": Remoteci.api_fields_without_api_secret},
    ]
)


_topic_relationships = [
    {"product": Product.api_fields},
    {"next_topic": Topic.api_fields_without_data},
]
Topic.api_fields.extend(_topic_relationships)
Topic.api_fields_without_data.extend(_topic_relationships)


_component_relationships = [
    {"topic": Topic.api_fields_without_data},
    {"jobs": Job.api_fields_without_data},
    {"files": Componentfile.api_fields},
]
Component.api_fields.extend(_component_relationships)
Component.api_fields_without_data.extend(_component_relationships)


_feeder_relationships = [
    {"team": Team.api_fields},
]
Feeder.api_fields.extend(_feeder_relationships)
Feeder.api_fields_without_api_secret.extend(_feeder_relationships)


Jobstate.api_fields.extend(
    [
        {"files": File.api_fields},
    ]
)


Pipeline.api_fields.extend(
    [
        {"team": Team.api_fields},
    ]
)


Product.api_fields.extend(
    [
        {"teams": Team.api_fields},
        {"topics": Topic.api_fields_without_data},
    ]
)


_remoteci_relationships = [
    {"team": Team.api_fields},
    {"users": User.api_fields},
]
Remoteci.api_fields.extend(_remoteci_relationships)
Remoteci.api_fields_without_api_secret.extend(_remoteci_relationships)
