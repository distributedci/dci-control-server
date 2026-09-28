# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

JUNIT = """<testsuite errors="1" failures="1" name="pytest" skipped="1" tests="6" time="4.04239122">
    <testcase classname="classname_1" name="test_1" time="0.02311568802">
        <skipped message="skip message" type="skipped">test skipped</skipped>
    </testcase>
    <testcase classname="classname_1" name="test_2" time="0.91562318802">
        <error message="error message" type="error">test in error</error>
    </testcase>
    <testcase classname="classname_1" name="test_3" time="0.18802915623">
        <failure message="failure message" type="failure">test in failure</failure>
    </testcase>
    <testcase classname="classname_1" name="test_4" time="2.91562318802"/>
    <testcase classname="classname_1" name="test_5" time="3.23423443444">
        <system-out>STDOUT</system-out>
    </testcase>
    <testcase classname="classname_1" name="test_6" time="2.48294832443">
        <system-err>STDERR</system-err>
    </testcase>
</testsuite>
"""

JUNIT_with_properties = """<testsuite errors="1" failures="1" name="pytest" skipped="1" tests="6" time="4.04239122">
    <properties>
        <property name="p1" value="v1"></property>
        <property name="p2" value="v2"></property>
    </properties>
    <testcase classname="classname_1" name="test_1" time="0.02311568802">
        <skipped message="skip message" type="skipped">test skipped</skipped>
        <properties>
            <property name="p3" value="v3"></property>
            <property name="p4" value="v4"></property>
        </properties>
    </testcase>
    <testcase classname="classname_1" name="test_2" time="0.91562318802">
        <error message="error message" type="error">test in error</error>
        <properties>
            <property name="p5" value="v5"></property>
            <property name="p6" value="v6"></property>
        </properties>
    </testcase>
    <testcase classname="classname_1" name="test_3" time="0.18802915623">
        <failure message="failure message" type="failure">test in failure</failure>
        <properties></properties>
    </testcase>
    <testcase classname="classname_1" name="test_4" time="2.91562318802"/>
    <testcase classname="classname_1" name="test_5" time="3.23423443444">
        <system-out>STDOUT</system-out>
        <properties></properties>
    </testcase>
    <testcase classname="classname_1" name="test_6" time="2.48294832443">
        <system-err>STDERR</system-err>
        <properties></properties>
    </testcase>
</testsuite>
"""

JUNIT_with_testcase_properties = """<testsuite errors="1" failures="1" name="pytest" skipped="1" tests="6" time="4.04239122">
    <testcase classname="classname_1" name="test_1" time="0.02311568802">
        <skipped message="skip message" type="skipped">test skipped</skipped>
        <properties>
            <property name="p3" value="v3"></property>
            <property name="p4" value="v4"></property>
        </properties>
    </testcase>
    <testcase classname="classname_1" name="test_2" time="0.91562318802">
        <error message="error message" type="error">test in error</error>
        <properties>
            <property name="p5" value="v5"></property>
            <property name="p6" value="v6"></property>
        </properties>
    </testcase>
    <testcase classname="classname_1" name="test_3" time="0.18802915623">
        <failure message="failure message" type="failure">test in failure</failure>
    </testcase>
    <testcase classname="classname_1" name="test_4" time="2.91562318802"/>
    <testcase classname="classname_1" name="test_5" time="3.23423443444">
        <system-out>STDOUT</system-out>
    </testcase>
    <testcase classname="classname_1" name="test_6" time="2.48294832443">
        <system-err>STDERR</system-err>
    </testcase>
</testsuite>
"""

JUNIT_with_testcase_properties_updated = """<testsuite errors="1" failures="1" name="pytest" skipped="1" tests="6" time="4.04239122">
    <testcase classname="classname_1" name="test_1" time="0.02311568802">
        <skipped message="skip message" type="skipped">test skipped</skipped>
        <properties>
            <property name="p3" value="v3-updated"></property>
        </properties>
    </testcase>
    <testcase classname="classname_1" name="test_2" time="0.91562318802">
        <error message="error message" type="error">test in error</error>
        <properties>
            <property name="p6" value="v6"></property>
        </properties>
    </testcase>
    <testcase classname="classname_1" name="test_3" time="0.18802915623">
        <failure message="failure message" type="failure">test in failure</failure>
    </testcase>
    <testcase classname="classname_1" name="test_4" time="2.91562318802"/>
    <testcase classname="classname_1" name="test_5" time="3.23423443444">
        <system-out>STDOUT</system-out>
    </testcase>
    <testcase classname="classname_1" name="test_6" time="2.48294832443">
        <system-err>STDERR</system-err>
    </testcase>
</testsuite>
"""

jobtest_one = """
<testsuite errors="0" failures="0" name="Kikoolol1" tests="3" time="127.0">
    <testcase
            classname="Testsuite_1"
            name="test_1"
            time="30">
            <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase
            classname="Testsuite_1"
            name="test_2"
            time="40">
    </testcase>
    <testcase
            classname="Testsuite_1"
            name="test_3[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]"
            time="40">
    </testcase>
</testsuite>
"""

jobtest_two = """
<testsuite errors="1" failures="1" name="Kikoolol1" tests="3" time="3385.127">
    <testcase
            classname="Testsuite_1"
            name="test_1"
            time="36">
    </testcase>
    <testcase
            classname="Testsuite_1"
            name="test_2"
            time="30">
    </testcase>
    <testcase
            classname="Testsuite_1"
            name="test_3[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]"
            time="50">
        <failure type="Exception">Traceback</failure>
    </testcase>
</testsuite>
"""
