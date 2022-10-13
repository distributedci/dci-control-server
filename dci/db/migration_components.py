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
import re


def _get_component_name_version_separator(component_name):
    separator = None
    for sep in [":", "@", " "]:
        if sep in component_name:
            separator = sep
            break
    return separator


def _is_sha1(s):
    pattern = r"^[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, s))


def _get_component_name(name, canonical_project_name):
    if name in canonical_project_name:
        return canonical_project_name
    return canonical_project_name if _is_sha1(name) else name


def get_component_version(name, canonical_project_name):
    component_name = _get_component_name(name, canonical_project_name)
    if "RHOS" in name:
        version = component_name.rsplit("RHOS-", 1)[-1]
        if version.count("-") == 3:
            return version.rsplit("-", 1)[0]
        return version
    if "RHEL" in name:
        return component_name.rsplit("RHEL-", 1)[-1]
    separator = _get_component_name_version_separator(component_name)
    if separator is None:
        return ""
    return component_name.rsplit(separator, 1)[-1]


def get_component_display_name(name, canonical_project_name):
    if "RHOS" in name or "RHEL" in name:
        return name
    component_name = _get_component_name(name, canonical_project_name)
    separator = _get_component_name_version_separator(component_name)
    if separator is None:
        return component_name
    return component_name.rsplit(separator, 1)[0]
