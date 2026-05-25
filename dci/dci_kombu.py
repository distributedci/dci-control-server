# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2024 Red Hat, Inc
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

import kombu
import socket
from datetime import datetime, timezone
from dci import dci_config
from dci.common import notifications

import logging

logger = logging.getLogger(__name__)


DCI_EXCHANGE = "dci.exchange"
RK_JOBS_CREATED = "dci.jobs.created"
RK_JOBS_UPDATED = "dci.jobs.updated"
RK_JOBS_FINISHED = "dci.jobs.finished"
RK_FILES_CREATED = "dci.files.created"
RK_COMPONENTS_CREATED = "dci.components.created"
RK_COMPONENTS_UPDATED = "dci.components.updated"

QUEUE_JOBS_CREATED = "jobs_created"
QUEUE_JOBS_UPDATED = "jobs_updated"
QUEUE_JOBS_FINISHED = "jobs_finished"
QUEUE_FILES_CREATED = "files_created"
QUEUE_COMPONENTS_CREATED = "components_created"
QUEUE_COMPONENTS_UPDATED = "components_updated"

QUEUE_NAMES_ROUTING_KEYS = [
    {"name": QUEUE_JOBS_CREATED, "routing_key": RK_JOBS_CREATED},
    {"name": QUEUE_JOBS_UPDATED, "routing_key": RK_JOBS_UPDATED},
    {"name": QUEUE_JOBS_FINISHED, "routing_key": RK_JOBS_FINISHED},
    {"name": QUEUE_FILES_CREATED, "routing_key": RK_FILES_CREATED},
    {"name": QUEUE_COMPONENTS_CREATED, "routing_key": RK_COMPONENTS_CREATED},
    {"name": QUEUE_COMPONENTS_UPDATED, "routing_key": RK_COMPONENTS_UPDATED},
]


class KombuProducer:
    def __init__(self):
        super(KombuProducer, self).__init__()
        self._connection = kombu.Connection(dci_config.CONFIG["AMQP_BROKER_URL"])
        self._dci_exchange = kombu.Exchange(DCI_EXCHANGE, type="topic")
        self._producer = None

    def _get_producer(self):
        if not self._producer:
            channel = self._connection.channel()
            self._producer = kombu.Producer(channel=channel, serializer="json")
        return self._producer

    def _publish(self, message, routing_key):
        try:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"Publishing message: {message} to routing key: {routing_key}")
            return self._get_producer().publish(
                message,
                exchange=self._dci_exchange,
                routing_key=routing_key,
                headers={"routing_key": routing_key},
            )
        except (OSError, socket.gaierror, Exception) as e:
            _msg = self._error_mail(str(e))
            notifications.send_alert_mail(
                subject="RabbitMQ transport error",
                message=_msg,
            )
            logger.exception("error while trying to publish a message.")

    def _error_mail(self, exc):

        return f"""
You are receiving this email because the DCI control server failed to send a message to RabbitMQ.

Exception traceback:

{exc}

"""

    def publish_jobs_created(self, message):
        self._publish(message, RK_JOBS_CREATED)

    def publish_jobs_updated(self, message):
        self._publish(message, RK_JOBS_UPDATED)

    def publish_jobs_finished(self, message):
        self._publish(message, RK_JOBS_FINISHED)

    def publish_files_created(self, message):
        self._publish(message, RK_FILES_CREATED)

    def publish_components_created(self, message):
        self._publish(message, RK_COMPONENTS_CREATED)

    def publish_components_updated(self, message):
        self._publish(message, RK_COMPONENTS_UPDATED)
