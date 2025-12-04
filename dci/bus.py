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

import logging

from dci import dci_config
from dci.api.v1 import notifications

import flask
import kombu
import socket


logger = logging.getLogger(__name__)


def send_job_event(job: dict):
    if job["status"] == "new":
        flask.g.bus.publish("dci.jobs.started", job)
    elif job["status"] in ["pre-run", "running", "post-run"]:
        flask.g.bus.publish({"event": "job_updated", "job": job})
    elif job["status"] in ["killed", "failure", "error"]:
        flask.g.bus.publish("dci.jobs.failed", job)
    elif job["status"] == "success":
        flask.g.bus.publish("dci.jobs.successful", job)


class MessageBus:
    def __init__(self, broker_url, exchange_name):
        logger.info(
            f"Configuring Kombu on broker {broker_url} and exchange {exchange_name}"
        )
        self.connection = kombu.Connection(
            broker_url,
            transport_options={"confirm_publish": True},
        )
        self.exchange = kombu.Exchange(exchange_name, type="direct")
        self.producer = None

    def _ensure_producer(self):
        if not self.producer:
            channel = self.connection.channel()
            self.producer = kombu.Producer(
                exchange=self.exchange,
                channel=channel,
            )

    def publish(self, message):
        try:
            self._ensure_producer()
            for queue,key in self.queues_and_keys:
                self.producer.publish(
                    message,
                    routing_key=key,
                    serializer="json",
                )
                queue.maybe_bind(self._connection)
                queue.declare()
        except Exception as e:
            logger.error("Error while trying to publish a message")
            logger.exception(e)
            message = f"""
You are receiving this email because the DCI control server failed to send a message to RabbitMQ.

Exception traceback:

{str(e)}

"""
            notifications.send_alert_mail(
                subject="RabbitMQ transport error",
                message=message,
            )


class KombuProducer:
    def __init__(self):
        self._connection = kombu.Connection(
            dci_config.CONFIG["AMQP_BROKER_URL"],
            transport_options={"confirm_publish": True},
        )
        self._exchange = kombu.Exchange("dci.analytics.exchange", type="direct")
        self._queue = kombu.Queue(
            name="dci.analytics.queue",
            exchange=self._exchange,
            routing_key="dci.analytics.jobs",
        )
        self._queue.maybe_bind(self._connection)
        self._queue.declare()
        self._producer = None

    def _error_mail(self, exc):

        return f"""
You are receiving this email because the DCI control server failed to send a message to RabbitMQ.

Exception traceback:

{exc}

"""

    def publish(self, message):
        try:
            if not self._producer:
                channel = self._connection.channel()
                self._producer = kombu.Producer(
                    exchange=self._exchange,
                    channel=channel,
                    routing_key="dci.analytics.jobs",
                )

            return self._producer.publish(message)
        except (OSError, socket.gaierror, Exception) as e:
            _msg = self._error_mail(str(e))
            notifications.send_alert_mail(
                subject="RabbitMQ transport error",
                message=_msg,
            )
            logger.exception("error while trying to publish a message.")
