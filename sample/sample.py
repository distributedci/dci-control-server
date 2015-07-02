#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import client

import random
import uuid


client = client.DCIClient(end_point="http://127.0.0.1:5000",
                          login="admin", password="admin")

for _ in range(10):
    product = client.post('/api/products',
                          data={'name': str(uuid.uuid4())[:18],
                                'data': {
                                'product_keys': {
                                    'foo': ['bar1', 'bar2']}}})
    product_id = product.json()["id"]

    for _ in range(5):
        version = client.post('/api/versions',
                              data={'name': str(uuid.uuid4())[:18],
                                    'product_id': product_id,
                                    'data': {
                                    'version_keys': {
                                        'foo': ['bar1', 'bar2']}}})
        version_id = version.json()["id"]

        test = client.post('/api/tests',
                           data={'name': 'bob',
                                 'data': {
                                     'test_keys': {
                                         'foo': ['bar1', 'bar2']}}})
        test_id = test.json()["id"]

        testversion = client.post('/api/testversions',
                                  data={
                                      'test_id': test_id,
                                      'version_id': version_id})
        testversion_id = testversion.json()["id"]

        remoteci = client.post('/api/remotecis',
                               data={
                                   'name': str(uuid.uuid4())[:18],
                                   'test_id': test_id,
                                   'data': {
                                       'remoteci_keys': {
                                           'foo': ['bar1', 'bar2']}}})
        remoteci_id = remoteci.json()["id"]

        job = client.post('/api/jobs',
                          data={'remoteci_id': remoteci_id})
        job_id = job.json()["id"]

        for _ in range(2):
            alea = random.randint(0, 2)
            status = ["ongoing", "failure", "success"][alea]
            jobstate = client.post('/api/jobstates',
                                   data={'job_id': job_id,
                                         'status': status})
            jobstate_id = jobstate.json()["id"]

            for _ in range(2):
                client.post('/api/files',
                            data={'jobstate_id': jobstate_id,
                                  'content': 'kikoolol! mdr! lol!' * 100,
                                  'name': str(uuid.uuid4())[:18],
                                  'mime': 'text'})

print("Database populated successfully :)\n")
