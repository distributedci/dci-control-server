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


def _get_version_delimiter(component_name):
    delimiter = None
    for c in [":", "@", " "]:
        if c in component_name:
            delimiter = c
            break
    return delimiter


def _is_sha1(s):
    pattern = r"^[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, s))


def _get_semver(version):
    match = re.match(r"^(\d+\.\d+\.\d+)", version)
    if match:
        return match.group(1)
    else:
        return version


def get_component_display_name_and_version(name, canonical_project_name):
    name_is_version = _is_sha1(name)

    component_name = (
        canonical_project_name
        if "OpenShift" in canonical_project_name
        or name in canonical_project_name
        or name_is_version
        else name
    )

    for short_name in ["RHOS", "RHEL"]:
        if short_name in component_name:
            version = component_name.rsplit("%s-" % short_name, 1)[-1]
            return component_name, version

    if "OpenShift" in canonical_project_name:
        display_name = " ".join(canonical_project_name.split(" ", 2)[:2])
        return display_name, name

    delimiter = _get_version_delimiter(component_name)
    if delimiter is None:
        return component_name, ""

    display_name, version = component_name.rsplit(delimiter, 1)
    if name_is_version:
        return "%s %s" % (display_name, name[0:7]), name

    display_name = "%s %s" % (display_name, _get_semver(version))
    return display_name, version
