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

import smtplib

import mock

from dci import dci_config
from dci.worker import mail_worker as m_w


def test_get_email_configuration():
    email_configuration = m_w.get_email_configuration()
    assert "host" in email_configuration
    assert "port" in email_configuration
    assert "account" in email_configuration
    assert "password" in email_configuration
    assert email_configuration["port"] == int(email_configuration["port"])
    assert email_configuration["use_tls"] == dci_config.CONFIG["DCI_EMAIL_USE_TLS"]


def test_build_job_email():
    job_event = {
        "topic_name": "topic",
        "remoteci_name": "remoteci",
        "status": "failure",
        "regressions": {},
        "job_id": "job_id",
        "components": ["component1", "component2"],
        "remoteci_id": "remoteci_id",
        "topic_id": "topic_id",
    }
    email = m_w.build_job_email("sender@example.com", job_event)
    assert email.get_payload(decode=True).decode("utf-8") == """
You are receiving this email because of the DCI job job_id for the
topic topic on the Remote CI remoteci.

The final status of the job is: failure

The components used are: component1, component2


For more information:
https://www.distributed-ci.io/jobs/job_id
"""


def test_send_mails():
    job_event = {
        "topic_name": "topic",
        "remoteci_name": "remoteci",
        "status": "failure",
        "regressions": {},
        "job_id": "job_id",
        "components": ["component1", "component2"],
        "remoteci_id": "remoteci_id",
        "topic_id": "topic_id",
    }
    email = m_w.build_job_email("sender@example.com", job_event)
    m_server = mock.MagicMock()
    m_w.send_mails(m_server, ["u1@example.com", "u2@example.com"], email)
    assert m_server.sendmail.call_count == 2


def test_send_mails_retries_failed_recipient_and_continues():
    job_event = {
        "topic_name": "topic",
        "remoteci_name": "remoteci",
        "status": "failure",
        "regressions": {},
        "job_id": "job_id",
        "components": ["component1", "component2"],
        "remoteci_id": "remoteci_id",
        "topic_id": "topic_id",
    }
    email = m_w.build_job_email("sender@example.com", job_event)
    server = mock.MagicMock()
    server.sendmail.side_effect = [
        smtplib.SMTPRecipientsRefused({"u1@example.com": (550, b"recipient rejected")}),
        {},
        {},
    ]

    m_w.send_mails(server, ["u1@example.com", "u2@example.com"], email)

    assert [call.args[1] for call in server.sendmail.call_args_list] == [
        "u1@example.com",
        "u1@example.com",
        "u2@example.com",
    ]


def test_send_mails_continues_after_both_recipient_attempts_fail():
    job_event = {
        "topic_name": "topic",
        "remoteci_name": "remoteci",
        "status": "failure",
        "regressions": {},
        "job_id": "job_id",
        "components": ["component1", "component2"],
        "remoteci_id": "remoteci_id",
        "topic_id": "topic_id",
    }
    email = m_w.build_job_email("sender@example.com", job_event)
    server = mock.MagicMock()
    rejected = smtplib.SMTPRecipientsRefused(
        {"u1@example.com": (550, b"recipient rejected")}
    )
    server.sendmail.side_effect = [rejected, rejected, {}]

    m_w.send_mails(server, ["u1@example.com", "u2@example.com"], email)

    assert [call.args[1] for call in server.sendmail.call_args_list] == [
        "u1@example.com",
        "u1@example.com",
        "u2@example.com",
    ]


def test_send_mails_reconnects_after_connection_loss():
    job_event = {
        "topic_name": "topic",
        "remoteci_name": "remoteci",
        "status": "failure",
        "regressions": {},
        "job_id": "job_id",
        "components": ["component1", "component2"],
        "remoteci_id": "remoteci_id",
        "topic_id": "topic_id",
    }
    email = m_w.build_job_email("sender@example.com", job_event)
    disconnected_server = mock.MagicMock()
    disconnected_server.sendmail.side_effect = smtplib.SMTPServerDisconnected(
        "connection lost"
    )
    reconnected_server = mock.MagicMock()
    server_factory = mock.Mock(return_value=reconnected_server)
    close_server = mock.Mock()

    m_w.send_mails(
        disconnected_server,
        ["u1@example.com", "u2@example.com"],
        email,
        smtp_server_factory=server_factory,
        close_smtp_server=close_server,
    )

    disconnected_server.sendmail.assert_called_once()
    assert [call.args[1] for call in reconnected_server.sendmail.call_args_list] == [
        "u1@example.com",
        "u2@example.com",
    ]
    server_factory.assert_called_once_with()
    assert close_server.call_args_list == [
        mock.call(disconnected_server),
        mock.call(reconnected_server),
    ]


def test_build_component_email():
    component_event = {
        "topic_name": "topic",
        "component_name": "component",
        "component_id": "component_id",
        "emails": ["u1@example.com", "u2@example.com"],
        "topic_id": "topic_id",
        "state": "active",
    }
    email = m_w.build_component_email("sender@example.com", component_event)
    assert email.get_payload(decode=True).decode("utf-8") == """
You are receiving this email because of the DCI topic topic.

A new component has been created:

  https://www.distributed-ci.io/topics/topic_id/components/component_id

"""
