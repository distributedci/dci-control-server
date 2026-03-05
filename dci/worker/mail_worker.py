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

import os

from dci.common import notifications

try:
    from email.MIMEText import MIMEText
except ImportError:
    from email.mime.text import MIMEText


def get_email_configuration():
    return {
        "server": os.getenv("DCI_EMAIL_SERVER"),
        "port": os.getenv("DCI_EMAIL_SERVER_PORT", 587),
        "account": os.getenv("DCI_FROM_EMAIL", "no-reply@distributed-ci.io"),
        "password": os.getenv("DCI_EMAIL_PASSWORD"),
    }


def build_job_email(sender, job_event):
    subject = "[DCI Status][%s][%s][%s]" % (
        job_event["topic_name"],
        job_event["remoteci_name"],
        job_event["status"],
    )
    message = notifications.format_job_mail_message(job_event)
    email = MIMEText(message)
    email["From"] = "Distributed-CI Notification <%s>" % sender
    email["subject"] = subject
    email["DCI-remoteci"] = job_event["remoteci_id"]
    email["DCI-topic"] = job_event["topic_id"]
    return email


def send_mails(server, recipients, email):
    for recipient in recipients:
        # email.message are not classic dict, a new affectation does
        # not overwrite the previous one.
        del email["To"]
        email["To"] = recipient
        server.sendmail(email["From"], email["To"], email.as_string())


def build_component_email(sender, component_event):
    subject = "[DCI Status][%s][%s][%s]" % (
        component_event["topic_name"],
        component_event["component_name"],
        component_event["state"],
    )
    message = notifications.format_component_mail_message(component_event)
    email = MIMEText(message)
    email["From"] = "Distributed-CI Notification <%s>" % sender
    email["subject"] = subject
    return email
