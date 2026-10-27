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
import smtplib

import mock
import pytest
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


def test_get_smtp_server_connects_once_and_configures_tls_and_login():
    smtp_server = mock.MagicMock()

    with mock.patch.object(
        run_mail_worker.smtplib, "SMTP", return_value=smtp_server
    ) as smtp:
        result = run_mail_worker._get_smtp_server(
            "smtp.example.com", 587, "sender@example.com", "secret", use_tls=True
        )

    assert result is smtp_server
    smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)
    smtp_server.connect.assert_not_called()
    smtp_server.starttls.assert_called_once_with()
    smtp_server.login.assert_called_once_with("sender@example.com", "secret")


def test_get_smtp_server_can_skip_tls_and_login():
    smtp_server = mock.MagicMock()

    with mock.patch.object(
        run_mail_worker.smtplib, "SMTP", return_value=smtp_server
    ) as smtp:
        result = run_mail_worker._get_smtp_server(
            "smtp.example.com", 25, None, None, use_tls=False
        )

    assert result is smtp_server
    smtp.assert_called_once_with("smtp.example.com", 25, timeout=10)
    smtp_server.starttls.assert_not_called()
    smtp_server.login.assert_not_called()


def test_get_smtp_server_retries_transient_connection_errors():
    smtp_server = mock.MagicMock()
    with mock.patch.object(
        run_mail_worker.smtplib,
        "SMTP",
        side_effect=[
            ConnectionRefusedError("refused"),
            TimeoutError("timed out"),
            smtp_server,
        ],
    ) as smtp, mock.patch.object(run_mail_worker.time, "sleep") as sleep:
        result = run_mail_worker._get_smtp_server("smtp.example.com", 587, None, None)

    assert result is smtp_server
    assert smtp.call_count == 3
    assert sleep.call_args_list == [mock.call(1), mock.call(2)]


def test_get_smtp_server_stops_after_three_transient_failures():
    with mock.patch.object(
        run_mail_worker.smtplib,
        "SMTP",
        side_effect=[
            ConnectionRefusedError("refused"),
            ConnectionRefusedError("refused"),
            ConnectionRefusedError("refused"),
        ],
    ) as smtp, mock.patch.object(run_mail_worker.time, "sleep") as sleep:
        with pytest.raises(ConnectionRefusedError):
            run_mail_worker._get_smtp_server("smtp.example.com", 587, None, None)

    assert smtp.call_count == 3
    assert sleep.call_args_list == [mock.call(1), mock.call(2)]


def test_get_smtp_server_closes_session_after_setup_failure():
    smtp_server = mock.MagicMock()
    smtp_server.starttls.side_effect = smtplib.SMTPNotSupportedError("no STARTTLS")

    with mock.patch.object(
        run_mail_worker.smtplib, "SMTP", return_value=smtp_server
    ) as smtp:
        with pytest.raises(smtplib.SMTPNotSupportedError):
            run_mail_worker._get_smtp_server(
                "smtp.example.com", 587, None, None, use_tls=True
            )

    smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)
    smtp_server.quit.assert_called_once_with()


def test_process_acknowledges_only_after_session_closes():
    session = _session_mock("session")
    events = []
    session.__exit__.side_effect = lambda *args: events.append("session closed")
    message = mock.Mock()
    message.ack.side_effect = lambda: events.append("acknowledged")
    worker = run_mail_worker.Worker(
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(return_value=session),
    )

    worker._process(message, lambda current_session: events.append("processed"))

    assert events == ["processed", "session closed", "acknowledged"]
    message.reject.assert_not_called()


def test_process_requeues_when_session_close_fails():
    session = _session_mock("session")
    session.__exit__.side_effect = RuntimeError("session close failed")
    message = mock.Mock()
    worker = run_mail_worker.Worker(
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(return_value=session),
    )

    worker._process(message, lambda current_session: None)

    message.ack.assert_not_called()
    message.reject.assert_called_once_with(requeue=True)


def test_smtp_close_error_does_not_fail_successful_send():
    smtp_server = mock.MagicMock()
    smtp_server.quit.side_effect = OSError("connection closed")

    with mock.patch.object(
        run_mail_worker, "_get_smtp_server", return_value=smtp_server
    ), mock.patch.object(run_mail_worker.m_w, "send_mails") as send_mails:
        run_mail_worker._send_event_email({}, ["recipient@example.com"], mock.Mock())

    send_mails.assert_called_once_with(
        smtp_server, ["recipient@example.com"], mock.ANY
    )
    smtp_server.quit.assert_called_once_with()
    smtp_server.close.assert_called_once_with()


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


def test_failed_message_is_requeued_and_next_message_uses_a_new_session():
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
    first_message.ack.assert_not_called()
    first_message.reject.assert_called_once_with(requeue=True)
    second_message.ack.assert_called_once_with()
    second_message.reject.assert_not_called()


def test_partial_email_send_failure_requeues_message_and_closes_smtp():
    session = _session_mock("session")
    worker = run_mail_worker.Worker(
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(return_value=session),
    )
    smtp_server = mock.MagicMock()
    smtp_server.sendmail.side_effect = [
        {},
        smtplib.SMTPRecipientsRefused(
            {"second@example.com": (550, b"recipient rejected")}
        ),
    ]
    component_event = {
        "state": "active",
        "emails": ["first@example.com", "second@example.com"],
        "topic_name": "topic",
        "component_name": "component",
        "component_id": "component-id",
        "topic_id": "topic-id",
    }
    message = mock.Mock()
    payload = {"component_id": "component-id"}

    with mock.patch.object(
        run_mail_worker.a_d_l,
        "get_serialized_component",
        return_value={"id": "component-id", "topic_id": "topic-id"},
    ), mock.patch.object(
        run_mail_worker.a_d_l,
        "get_emails_subscribed_to_topic",
        return_value=[],
    ), mock.patch.object(
        run_mail_worker.notifications,
        "get_component_event",
        return_value=component_event,
    ), mock.patch.object(
        run_mail_worker.m_w,
        "get_email_configuration",
        return_value={
            "host": "smtp.example.com",
            "port": 587,
            "account": "sender@example.com",
            "password": None,
            "use_tls": True,
        },
    ), mock.patch.object(
        run_mail_worker, "_get_smtp_server", return_value=smtp_server
    ):
        worker.on_component_created(payload, message)

    assert smtp_server.sendmail.call_count == 2
    smtp_server.quit.assert_called_once_with()
    message.ack.assert_not_called()
    message.reject.assert_called_once_with(requeue=True)
