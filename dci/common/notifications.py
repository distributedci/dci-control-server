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

from dci import dci_config

import logging
import smtplib

try:
    from email.MIMEText import MIMEText
except ImportError:
    from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


def send_alert_mail(subject, message):
    def _send_mail():
        email_server = dci_config.CONFIG["DCI_EMAIL_SERVER"]
        port = dci_config.CONFIG["DCI_EMAIL_SERVER_PORT"]
        account = dci_config.CONFIG["DCI_FROM_EMAIL"]
        smtp_server = smtplib.SMTP(email_server, port)
        use_tls = dci_config.CONFIG["DCI_EMAIL_USE_TLS"]
        if use_tls:
            smtp_server.starttls()

        email = MIMEText(message)
        email["From"] = "Distributed-CI Notification <%s>" % account
        email["subject"] = subject
        email["To"] = dci_config.CONFIG["DCI_ALERT_EMAIL"]
        smtp_server.sendmail(email["From"], email["To"], email.as_string())
        smtp_server.quit()

    try:
        _send_mail()
    except Exception:
        logger.exception("error while sending notification mail")


def format_job_mail_message(job):
    # compute test name:regressions number
    regressions = ", ".join(
        ["%s: %s" % (k, v) for (k, v) in job["regressions"].items()]
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
        job_id=job["job_id"],
        topic=job["topic_name"],
        remoteci=job["remoteci_name"],
        status=job["status"],
        components=", ".join(job["components"]),
        regressions=regressions,
    )


def get_job_event(job, emails):
    if job["status"] == "success":
        return None

    if not emails:
        return None

    components_names = [c["name"] for c in job["components"]]
    regressions = {res["name"]: res["regressions"] for res in job["results"]}

    return {
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


def format_component_mail_message(component_event):
    return """
You are receiving this email because of the DCI topic {topic}.

A new component has been created:

  https://www.distributed-ci.io/topics/{topic_id}/components/{component_id}

""".format(
        topic=component_event["topic_name"],
        topic_id=component_event["topic_id"],
        component_id=component_event["component_id"],
    )


def get_component_event(component, emails):
    if not emails:
        return None

    return {
        "emails": emails,
        "component_id": str(component["id"]),
        "component_name": component["name"],
        "topic_name": component["topic"]["name"],
        "topic_id": str(component["topic_id"]),
        "state": component["state"],
    }
