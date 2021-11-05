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

from dci.api.v1 import base
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models2


def format_mail_message(mesg):
    # compute test name:regressions number
    regressions = ', '.join(['%s: %s' % (k, v)
                             for (k, v) in mesg['regressions'].items()])
    if regressions:
        regressions = 'The regressions found are: %s' % regressions

    return """
You are receiving this email because of the DCI job {job_id} for the
topic {topic} on the Remote CI {remoteci}.

The final status of the job is: {status}

The components used are: {components}
{regressions}

For more information:
https://www.distributed-ci.io/jobs/{job_id}
""".format(
        job_id=mesg['job_id'],
        topic=mesg['topic_name'],
        remoteci=mesg['remoteci_name'],
        status=mesg['status'],
        components=', '.join(mesg['components']),
        regressions=regressions)


def build_job_finished_event(job):
    return {
        "event": "job_finished",
        "type": "job_finished",
        "job": json.loads(json.dumps(job, cls=utils.JSONEncoder))
    }


def get_email_event(job, emails):

    if job['status'] == 'success':
        return None

    if not emails:
        return None

    components_names = [c['name'] for c in job['components']]
    regressions = {res['name']: res['regressions']
                   for res in job['results']}

    return {
        'event': 'notification',
        'emails': emails,
        'job_id': str(job['id']),
        'status': job['status'],
        'topic_id': str(job['topic_id']),
        'topic_name': job['topic']['name'],
        'remoteci_id': str(job['remoteci_id']),
        'remoteci_name': job['remoteci']['name'],
        'components': components_names,
        'regressions': regressions
    }


def dlrn(job):

    for component in job['components']:
        data = component['data']
        if 'dlrn' in data and data['dlrn']:
            if data['dlrn']['commit_hash'] and \
               data['dlrn']['distro_hash'] and \
               data['dlrn']['commit_branch']:
                msg = {
                    'event': 'dlrn_publish',
                    'status': job['status'],
                    'job_id': str(job['id']),
                    'topic_name': job['topic']['name'],
                    'dlrn': data['dlrn']
                }
                return msg

    return None


def get_emails(remoteci_id):

    try:
        remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)
        return [u.email for u in remoteci.users]
    except dci_exc.DCIException:
        return []


def send_events(events):
    flask.g.sender.send_json(events)


def dispatcher(job):
    print('rtiti')
    events = []
    emails = get_emails(job['remoteci_id'])
    email_event = get_email_event(job, emails)
    if email_event:
        events.append(email_event)

    dlrn_event = dlrn(job)
    if dlrn_event:
        events.append(dlrn_event)

    job_finished = build_job_finished_event(job)
    if job_finished:
        events.append(job_finished)

    if events:
        send_events(events)
