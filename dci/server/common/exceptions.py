# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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


class ServerError(Exception):
    """Exception raised when an error occurs."""


class NotFound(ServerError):
    """Exception raised when the caller request a resource which does
    not exist.
    """
    def __init__(self, message):
        super(NotFound, self).__init__("'%s' does not exist" % message)


class DCIException(Exception):
    """Exception raised for all errors on call REST API, customize
    error output
    """

    def __init__(self, message, payload=None, status_code=400):
        super(DCIException, self).__init__()
        self.status_code = status_code
        self.message = message
        self.payload = payload

    def to_dict(self):
        return {
            'status_code': self.status_code,
            'message': self.message,
            'payload': dict(self.payload or ())
        }
