#!/usr/bin/env python3
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
import os

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin


AMQP_BROKER_URL = os.getenv("AMQP_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
AMQP_EXCHANGE_NAME = os.getenv("AMQP_EXCHANGE_NAME", "dci.exchange")

logger = logging.getLogger(__name__)


class FailedJobConsumer(ConsumerMixin):
    def __init__(self, connection, queues):
        self.connection = connection
        self.queues = queues

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.queues, callbacks=[self.on_message])]

    def on_message(self, body, message):
        job = body

        message.ack()


if __name__ == "__main__":
    exchange = Exchange(AMQP_EXCHANGE_NAME, type="direct")
    queues = [Queue("dci.queues.jobs.failed", exchange, routing_key="dci.jobs.failed")]

    logging.info("Starting jobs consumers")
    with Connection(AMQP_BROKER_URL, heartbeat=4) as connection:
        consumer = FailedJobConsumer(connection, queues)
        consumer.run()
