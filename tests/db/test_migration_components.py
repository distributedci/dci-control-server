# -*- encoding: utf-8 -*-
#
# Copyright 2023 Red Hat, Inc.
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

from dci.db.migration_components import (
    get_component_version,
    get_component_display_name,
)


def test_component_migrations_methods():

    testcases = [
        {
            "name": "amazing-product:20.07.1",
            "canonical_project_name": "Partner amazing-product:20.07.1",
            "display_name": "Partner amazing-product",
            "version": "20.07.1",
        },
        {
            "name": "product:20.10",
            "canonical_project_name": "Partner product:20.10",
            "display_name": "Partner product",
            "version": "20.10",
        },
        {
            "name": "partner/product:14.7.0.4-0.71.7N0LIC",
            "canonical_project_name": "partner/product:14.7.0.4-0.71.7N0LIC",
            "display_name": "partner/product",
            "version": "14.7.0.4-0.71.7N0LIC",
        },
        {
            "name": "registry.abcdef.lab:4443/redhat/redhat-operator-index:v4.9",
            "canonical_project_name": "registry.abcdef.lab:4443/redhat/redhat-operator-index:v4.9",
            "display_name": "registry.abcdef.lab:4443/redhat/redhat-operator-index",
            "version": "v4.9",
        },
        {
            "name": "RHEL-9.1.0-20220812.1",
            "canonical_project_name": "RHEL-9.1.0-20220812.1",
            "display_name": "RHEL-9.1.0-20220812.1",
            "version": "9.1.0-20220812.1",
        },
        {
            "name": "RHOS-17.0-RHEL-9-20220816.n.2",
            "canonical_project_name": "17.0-RHEL-9",
            "display_name": "RHOS-17.0-RHEL-9-20220816.n.2",
            "version": "17.0-RHEL-9",
        },
        {
            "name": "RH7-RHOS-10.0 2017-05-23.4",
            "canonical_project_name": "RH7-RHOS-10.0",
            "display_name": "RH7-RHOS-10.0 2017-05-23.4",
            "version": "10.0 2017-05-23.4",
        },
        {
            "name": "CNF image nrf-expiration 10.1.0-4757-ubi-1-0",
            "canonical_project_name": "CNF image nrf-expiration 10.1.0-4757-ubi-1-0",
            "display_name": "CNF image nrf-expiration",
            "version": "10.1.0-4757-ubi-1-0",
        },
        {
            "name": "CNF img ocp-v4.0-art-dev@sha256 0.0.0+nil",
            "canonical_project_name": "CNF img ocp-v4.0-art-dev@sha256 0.0.0+nil",
            "display_name": "CNF img ocp-v4.0-art-dev",
            "version": "sha256 0.0.0+nil",
        },
        {
            "name": "d2ebdc12ee3fd9325f501c30a5f3982512a17da7",
            "canonical_project_name": "dci-openshift-agent d2ebdc1",
            "display_name": "dci-openshift-agent",
            "version": "d2ebdc1",
        },
        {
            "name": "dci-openshift-app-agent 0.5.1-1.202209291912git8520aea2.el8",
            "canonical_project_name": "dci-openshift-app-agent 0.5.1-1.202209291912git8520aea2.el8",
            "display_name": "dci-openshift-app-agent",
            "version": "0.5.1-1.202209291912git8520aea2.el8",
        },
        {
            "name": "oc client 4.11.7",
            "canonical_project_name": "oc client 4.11.7",
            "display_name": "oc client",
            "version": "4.11.7",
        },
        {
            "name": "4.18.0-305.65.1.el8_4.x86_64",
            "canonical_project_name": "rhcos_kernel 4.18.0-305.65.1.el8_4.x86_64",
            "display_name": "rhcos_kernel",
            "version": "4.18.0-305.65.1.el8_4.x86_64",
        },
    ]

    for testcase in testcases:
        assert (
            get_component_display_name(
                testcase["name"], testcase["canonical_project_name"]
            )
            == testcase["display_name"]
        )
        assert (
            get_component_version(testcase["name"], testcase["canonical_project_name"])
            == testcase["version"]
        )
