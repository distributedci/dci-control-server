# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import codecs
import os
import setuptools
import subprocess

from dci import version


# dcibuild can be loaded only when doing the sdist sub-command because
# dci-packaging is extracted at the same level. When doing the other
# sub-commands like build, we extract the version from version.py.
try:
    from dcibuild import sdist, get_version

    sdist.dci_mod = "dci"
except:
    sdist = None

    def get_version():
        from dci import version

        return version.__version__


def _get_requirements():
    requirements_path = "%s/%s" % (
        os.path.dirname(os.path.abspath(__file__)),
        "requirements.txt",
    )
    with open(requirements_path, "r") as f:
        requirements = f.read()
        return requirements.split("\n")


def _get_readme():
    readme_path = "%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "README.md")

    with codecs.open(readme_path, "r", encoding="utf8") as f:
        return f.read()


setuptools.setup(
    name="dci-control-server",
    version=get_version(),
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    author="Distributed ci team.",
    author_email="distributed-ci@redhat.com",
    description="Server which manage products deployments",
    long_description=_get_readme(),
    install_requires=_get_requirements(),
    url="https://github.com/redhat-cip/dci-control-server",
    license="Apache v2.0",
    include_package_data=True,
    package_data={"dci-control-server": ["alembic/alembic.ini", "data/*"]},
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: System :: Distributed Computing",
    ],
    scripts=["bin/dci-dbsync", "bin/dci-dbinit"],
    cmdclass={
        "sdist": sdist,
    },

)
