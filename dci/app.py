# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
from dci.api import v1 as api_v1
from dci.common import exceptions
from dci.common import utils
from dci.db import models2
from dci import dci_config

import flask
import logging
import sys
import time
import zmq

from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

zmq_sender = None


class DciControlServer(flask.Flask):
    def __init__(self):
        super(DciControlServer, self).__init__(__name__)
        self.config.update(dci_config.CONFIG)
        self.url_map.strict_slashes = False
        self.engine = dci_config.get_engine(self.config["SQLALCHEMY_DATABASE_URI"])
        self.sender = self._get_zmq_sender(self.config["ZMQ_CONN"])
        self.store = dci_config.get_store()
        session = sessionmaker(bind=self.engine)()
        self.team_admin_id = self._get_team_id(session, "admin")
        self.team_redhat_id = self._get_team_id(session, "Red Hat")
        self.team_epm_id = self._get_team_id(session, "EPM")
        session.close()

    def _get_zmq_sender(self, zmq_conn):
        global zmq_sender
        if not zmq_sender:
            zmq_sender = zmq.Context().socket(zmq.PUSH)
            zmq_sender.connect(zmq_conn)
        return zmq_sender

    def make_default_options_response(self):
        resp = super(DciControlServer, self).make_default_options_response()
        methods = ["GET", "POST", "PUT", "DELETE"]
        headers = resp.headers

        headers.add_header("Access-Control-Allow-Methods", ", ".join(methods))
        headers.add_header("Access-Control-Allow-Headers", self.config["X_HEADERS"])
        return resp

    def process_response(self, resp):
        headers = resp.headers
        headers.add_header("Access-Control-Expose-Headers", self.config["X_HEADERS"])
        headers.add_header("Access-Control-Allow-Origin", self.config["X_DOMAINS"])

        return super(DciControlServer, self).process_response(resp)

    def _get_team_id(self, session, name):
        team = session.query(models2.Team).filter(models2.Team.name == name).first()
        if team is None:
            print(
                "%s team not found. Please init the database"
                " with the '%s' team and 'admin' user." % (name, name)
            )
            sys.exit(1)
        return team.id


def configure_root_logger():
    conf = dci_config.CONFIG
    logging.basicConfig(level=conf.get("LOG_LEVEL", logging.INFO))

    dci_log_level = conf.get("DCI_LOG_LEVEL", logging.INFO)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(conf["LOG_FORMAT"])
    console_handler.setFormatter(formatter)
    console_handler.setLevel(dci_log_level)

    root_logger = logging.getLogger()
    # remove all handlers before adding the console handler
    del root_logger.handlers[:]
    root_logger.addHandler(console_handler)


def werkzeug_logger_to_error():
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel("ERROR")


def create_app(param=None):
    dci_app = DciControlServer()
    dci_app.url_map.converters["uuid"] = utils.UUIDConverter

    werkzeug_logger_to_error()
    configure_root_logger()

    logger.info("dci control server startup")

    def handle_api_exception(api_exception):
        response = flask.jsonify(api_exception.to_dict())
        response.status_code = api_exception.status_code
        logger.exception(api_exception)
        return response

    def handle_dbapi_exception(dbapi_exception):
        db_exception = exceptions.DCIException(str(dbapi_exception)).to_dict()
        response = flask.jsonify(db_exception)
        response.status_code = 400
        logger.exception(dbapi_exception)
        return response

    @dci_app.before_request
    def before_request():
        flask.g.team_admin_id = dci_app.team_admin_id
        flask.g.team_redhat_id = dci_app.team_redhat_id
        flask.g.team_epm_id = dci_app.team_epm_id

        for i in range(5):
            try:
                flask.g.engine = dci_app.engine
                flask.g.db_conn = dci_app.engine.connect()
                flask.g.session = sessionmaker(bind=dci_app.engine)()
                break
            except Exception:
                logging.warning(
                    "failed to connect to the database, " "will retry in 1 second..."
                )
                time.sleep(1)
                pass
        flask.g.store = dci_app.store
        flask.g.sender = dci_app.sender

    @dci_app.teardown_request
    def teardown_request(_):
        try:
            flask.g.session.close()
        except Exception:
            logging.warning(
                "There's been an arror while calling session.close() in teardown_request."
            )

        try:
            flask.g.db_conn.close()
        except Exception:
            logging.warning(
                "There's been an error while calling db_conn.close() in teardown_request."
            )

    # Registering REST error handler
    dci_app.register_error_handler(exceptions.DCIException, handle_api_exception)
    dci_app.register_error_handler(sa_exc.DBAPIError, handle_dbapi_exception)

    # Registering REST API v1
    dci_app.register_blueprint(api_v1.api, url_prefix="/api/v1")

    # Registering custom encoder
    dci_app.json_encoder = utils.JSONEncoder

    return dci_app
