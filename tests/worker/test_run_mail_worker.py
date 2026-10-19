# -*- encoding: utf-8 -*-
#
# Copyright Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import importlib.machinery
import importlib.util
import os

import mock
import sqlalchemy.exc

from dci import dci_config


def _load_run_mail_worker():
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "bin", "run-mail-worker")
    )
    loader = importlib.machinery.SourceFileLoader("run_mail_worker", path)
    spec = importlib.util.spec_from_loader("run_mail_worker", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


run_mail_worker = _load_run_mail_worker()


def test_get_engine_pool_pre_ping_defaults_to_false():
    engine = dci_config.get_engine("postgresql+psycopg://dci:dci@127.0.0.1/dci")
    try:
        assert engine.pool._pre_ping is False
    finally:
        engine.dispose()


def test_mail_worker_engine_enables_pool_pre_ping():
    factory = run_mail_worker.get_session_factory()
    engine = factory.kw["bind"]
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()


def _session_mock(name):
    session = mock.MagicMock(name=name)
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    return session


def test_failed_message_closes_session_and_next_message_uses_a_new_session():
    failed = _session_mock("failed_session")
    recovered = _session_mock("recovered_session")
    factory = mock.Mock(side_effect=[failed, recovered])
    worker = run_mail_worker.Worker(
        mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock(), factory
    )
    seen = []

    def get_serialized_component(session, component_id):
        seen.append(session)
        if session is failed:
            raise sqlalchemy.exc.OperationalError(
                "SELECT components",
                {},
                Exception("server closed the connection unexpectedly"),
            )
        return {"id": component_id, "topic_id": "topic-id", "state": "active"}

    payload = {
        "component_id": "bd034de0-9507-4ba4-b90c-e56b5c858837",
        "previous_state": "inactive",
        "state": "active",
    }
    first_message = mock.Mock()
    second_message = mock.Mock()

    with mock.patch.object(
        run_mail_worker.a_d_l,
        "get_serialized_component",
        side_effect=get_serialized_component,
    ), mock.patch.object(
        run_mail_worker.a_d_l,
        "get_emails_subscribed_to_topic",
        return_value=[],
    ), mock.patch.object(
        run_mail_worker.notifications, "get_component_event", return_value=None
    ):
        worker.on_component_updated(payload, first_message)
        worker.on_component_updated(payload, second_message)

    assert seen == [failed, recovered]
    failed.__exit__.assert_called_once()
    recovered.__exit__.assert_called_once()
    first_message.ack.assert_called_once_with()
    second_message.ack.assert_called_once_with()
