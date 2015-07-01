# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

import base64
import json
import shutil
import subprocess
import tempfile
import time

import testtools


class DCITestCase(testtools.TestCase):

    def setUp(self):
        super(DCITestCase, self).setUp()
        self._db_dir = tempfile.mkdtemp()
        subprocess.call(['initdb', '--no-locale', self._db_dir])
        subprocess.call(['sed', '-i',
                         "s,#listen_addresses.*,listen_addresses = '',",
                         '%s/postgresql.conf' % self._db_dir])
        self._pg = subprocess.Popen(['postgres', '-F',
                                     '-k', self._db_dir,
                                     '-D', self._db_dir])
        time.sleep(1)
        subprocess.call(['psql', '--quiet',
                         '--echo-hidden', '-h', self._db_dir,
                         '-f', 'db_schema/dci-control-server.sql',
                         'template1'])
        time.sleep(2)
        db_uri = "postgresql:///?host=%s&dbname=template1" % self._db_dir
        import server.app
        self.app = server.app.create_app(db_uri)
        self.app.config['TESTING'] = True
        self.test_client = self.app.test_client()

    def tearDown(self):
        super(DCITestCase, self).tearDown()
        self._pg.kill()
        time.sleep(2)
        shutil.rmtree(self._db_dir)

    def client_call(self, method, username, password, path, **argv):
        encoded_basic_auth = base64.b64encode(
            ("%s:%s" % (
                username, password)).encode('ascii')).decode('utf-8')

        headers = {
            'Authorization': 'Basic ' + encoded_basic_auth,
            'Content-Type': 'application/json'
        }
        method_func = getattr(self.test_client, method)
        if 'data' in argv:
            argv['data'] = json.dumps(argv['data'])
        return method_func(path, headers=headers, **argv)

    def admin_client(self, method, path, **argv):
        return self.client_call(method, 'admin', 'admin', path, **argv)

    def partner_client(self, method, path, **argv):
        return self.client_call(method, 'partner', 'partner', path, **argv)

    def unauthorized_client(self, method, path, **argv):
        return self.client_call(method, 'admin', 'bob', path, **argv)

    def assertHTTPCode(self, result, code):
        return self.assertEqual(result.status_code, code)

    @staticmethod
    def _extract_response(rv):
        return json.loads(rv.get_data().decode())

    def _create_product(self):
        return self.admin_client(
            'post',
            '/api/products',
            data={'name': 'bob',
                  'data': {
                      'product_keys': {
                          'foo': ['bar1', 'bar2']}}})

    def _create_version(self, product_id):
        return self.admin_client(
            'post',
            '/api/versions',
            data={'name': 'bob',
                  'product_id': product_id,
                  'data': {
                      'version_keys': {
                          'foo': ['bar1', 'bar2']}}})

    def _create_test(self):
        return self.admin_client(
            'post',
            '/api/tests',
            data={
                'name': 'bob',
                'data': {
                    'test_keys': {
                        'foo': ['bar1', 'bar2']}}})

    def _create_testversion(self, test_id, version_id):
        return self.admin_client(
            'post',
            '/api/testversions',
            data={
                'test_id': test_id,
                'version_id': version_id})

    def _create_remoteci(self, test_id):
        return self.admin_client(
            'post',
            '/api/remotecis',
            data={
                'name': 'a_remoteci',
                'test_id': test_id,
                'data': {
                    'remoteci_keys': {
                        'foo': ['bar1', 'bar2']}}})

    def _create_job(self, remoteci_id):
        return self.partner_client(
            'post',
            '/api/jobs',
            data={'remoteci_id': remoteci_id})
