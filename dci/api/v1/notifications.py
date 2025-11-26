# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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
import json
import flask
import logging
import smtplib

from dci import dci_config
from dci.api.v1 import base
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models2


try:
    from email.MIMEText import MIMEText
except ImportError:
    from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def format_job_mail_message(mesg):
    # compute test name:regressions number
    regressions = ", ".join(
        ["%s: %s" % (k, v) for (k, v) in mesg["regressions"].items()]
    )
    if regressions:
        regressions = "The regressions found are: %s" % regressions

    return """
You are receiving this email because of the DCI job {job_id} for the
topic {topic} on the Remote CI {remoteci}.

The final status of the job is: {status}

The components used are: {components}
{regressions}

For more information:
https://www.distributed-ci.io/jobs/{job_id}
""".format(
        job_id=mesg["job_id"],
        topic=mesg["topic_name"],
        remoteci=mesg["remoteci_name"],
        status=mesg["status"],
        components=", ".join(mesg["components"]),
        regressions=regressions,
    )


def format_component_mail_message(event):
    return """
You are receiving this email because of the DCI topic {topic}.

A new component has been created:

  https://www.distributed-ci.io/topics/{topic_id}/components/{component_id}

""".format(
        topic=event["topic_name"],
        topic_id=event["topic_id"],
        component_id=event["component_id"],
    )


def build_job_finished_umb_event(job):
    return {
        "event": "job_finished",
        "type": "job_finished",
        "job": json.loads(json.dumps(job, cls=utils.JSONEncoder)),
    }


def get_job_event(job, emails):
    if job["status"] == "success":
        return None

    if not emails:
        return None

    components_names = [c["name"] for c in job["components"]]
    regressions = {res["name"]: res["regressions"] for res in job["results"]}

    return {
        "event": "notification",
        "emails": emails,
        "job_id": str(job["id"]),
        "status": job["status"],
        "topic_id": str(job["topic_id"]),
        "topic_name": job["topic"]["name"],
        "remoteci_id": str(job["remoteci_id"]),
        "remoteci_name": job["remoteci"]["name"],
        "components": components_names,
        "regressions": regressions,
    }


def dlrn(job):
    for component in job["components"]:
        data = component["data"]
        if "dlrn" in data and data["dlrn"]:
            if (
                data["dlrn"]["commit_hash"]
                and data["dlrn"]["distro_hash"]
                and data["dlrn"]["commit_branch"]
            ):
                msg = {
                    "event": "dlrn_publish",
                    "status": job["status"],
                    "job_id": str(job["id"]),
                    "topic_name": job["topic"]["name"],
                    "dlrn": data["dlrn"],
                }
                return msg

    return None


def get_emails_from_remoteci(remoteci_id):
    try:
        remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)
        return [u.email for u in remoteci.users]
    except dci_exc.DCIException:
        return []


def send_events(events):
    flask.g.sender.send_json(events)


def _handle_job_event(job):
    events = []
    emails = get_emails_from_remoteci(job["remoteci_id"])
    job_event = get_job_event(job, emails)
    if job_event:
        events.append(job_event)

    dlrn_event = dlrn(job)
    if dlrn_event:
        events.append(dlrn_event)

    umb_job_finished_event = build_job_finished_umb_event(job)
    if umb_job_finished_event:
        events.append(umb_job_finished_event)

    if events:
        send_events(events)


def get_emails_from_topic(topic_id):
    try:
        query = (
            flask.g.session.query(models2.User.email)
            .join(models2.UserTopic)
            .filter(models2.UserTopic.topic_id == topic_id)
        )
        return [um[0] for um in query.all()]
    except dci_exc.DCIException:
        return []


def get_component_event(component, emails):
    if not emails:
        return None

    return {
        "event": "component_notification",
        "emails": emails,
        "component_id": str(component["id"]),
        "component_name": component["name"],
        "topic_name": component["topic_name"],
        "topic_id": str(component["topic_id"]),
        "status": "new",
    }


def _handle_component_event(component):
    emails = get_emails_from_topic(component["topic_id"])
    component_event = get_component_event(component, emails)
    if component_event:
        send_events([component_event])


def job_dispatcher(job):
    _handle_job_event(job)


def component_dispatcher(component):
    _handle_component_event(component)


def publish(payload):
    return flask.g.messaging.publish(payload)


def send_alert_mail(subject, message):
    def _send_mail():
        email_server = dci_config.CONFIG.get("DCI_EMAIL_SERVER", "smtp.corp.redhat.com")
        port = dci_config.CONFIG.get("DCI_EMAIL_SERVER_PORT", 587)
        account = (
            dci_config.CONFIG.get("DCI_EMAIL_ACCOUNT", "no-reply@distributed-ci.io"),
        )
        smtp_server = smtplib.SMTP(email_server, port)
        use_tls = dci_config.CONFIG.get("DCI_EMAIL_USE_TLS", True)
        if use_tls:
            smtp_server.starttls()

        email = MIMEText(message)
        email["From"] = "Distributed-CI Notification <%s>" % account
        email["subject"] = subject
        email["To"] = dci_config.CONFIG.get(
            "DCI_EMAIL_ALERT", "distributedci+alerts@redhat.com"
        )
        smtp_server.sendmail(email["From"], email["To"], email.as_string())
        smtp_server.quit()

    try:
        _send_mail()
    except Exception:
        logger.exception("error while sending notification mail")
