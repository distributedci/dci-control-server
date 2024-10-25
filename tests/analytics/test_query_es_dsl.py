# -*- encoding: utf-8 -*-
#
# Copyright (C) 2024 Red Hat, Inc.
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

from dci.analytics import query_es_dsl as qed

import pyparsing as pp
import pytest


def test_parse_query_invalid():
    with pytest.raises(pp.ParseException):
        qed.parse("toto")


def test_parse_query_valid():
    ret = qed.parse("f1=v1")
    assert ret == ["f1", "=", "v1"]

    ret = qed.parse("(f1=v1)")
    assert ret == [["f1", "=", "v1"]]

    ret = qed.parse("(f1=v1) and (f2=v2)")
    assert ret == [["f1", "=", "v1"], "and", ["f2", "=", "v2"]]

    ret = qed.parse("((f1=v1) and (f2=v2)) or (f3=v3)")
    assert ret == [
        [["f1", "=", "v1"], "and", ["f2", "=", "v2"]],
        "or",
        ["f3", "=", "v3"],
    ]

    ret = qed.parse("((f1=v1) and (f2=v2)) or ((f3=v3) and (f4=v4))")
    assert ret == [
        [["f1", "=", "v1"], "and", ["f2", "=", "v2"]],
        "or",
        [["f3", "=", "v3"], "and", ["f4", "=", "v4"]],
    ]

    ret = qed.parse("((f1=v1) and ((f2=v2) or (f2=v22))) or ((f3=v3) and (f4=v4))")
    assert ret == [
        [["f1", "=", "v1"], "and", [["f2", "=", "v2"], "or", ["f2", "=", "v22"]]],
        "or",
        [["f3", "=", "v3"], "and", ["f4", "=", "v4"]],
    ]

    ret = qed.parse(
        "((f1=v1) and ((f2=v2) or (f2=v22))) or ((f3=v3) and ((f4=v4) or (f4=v44)))"
    )
    assert ret == [
        [["f1", "=", "v1"], "and", [["f2", "=", "v2"], "or", ["f2", "=", "v22"]]],
        "or",
        [["f3", "=", "v3"], "and", [["f4", "=", "v4"], "or", ["f4", "=", "v44"]]],
    ]

    ret = qed.parse("(f1=v1) and (name not_in [lol, kikoolol, lolipop])")
    assert ret == [
        ["f1", "=", "v1"],
        "and",
        ["name", "not_in", ["lol", "kikoolol", "lolipop"]],
    ]

    """
    ret = qed.parse("(f1=v1) and (f2=v2) and (f3=v3) and (f4=v4)")
    assert ret == [
        ["f1", "=", "v1"],
        "and",
        ["f2", "=", "v2"],
        "and",
        ["f3", "=", "v3"],
        "and",
        ["f4", "=", "v4"],
    ]"""


def test_build():
    ret = qed.build("f1=v1")
    assert ret == {"term": {"f1": "v1"}}

    ret = qed.build("(f1=v1)")
    assert ret == {"term": {"f1": "v1"}}

    ret = qed.build("(f1=v1) and (f2=v2)")
    assert ret == {"bool": {"filter": [{"term": {"f1": "v1"}}, {"term": {"f2": "v2"}}]}}

    ret = qed.build("((f1=v1) and (f2=v2)) or (f3=v3)")
    assert ret == {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "filter": [{"term": {"f1": "v1"}}, {"term": {"f2": "v2"}}]
                        }
                    },
                    {"term": {"f3": "v3"}},
                ]
            }
    }

    ret = qed.build("((f1=v1) and (f2=v2)) or ((f3=v3) and (f4=v4))")
    assert ret == {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "filter": [{"term": {"f1": "v1"}}, {"term": {"f2": "v2"}}]
                        }
                    },
                    {
                        "bool": {
                            "filter": [{"term": {"f3": "v3"}}, {"term": {"f4": "v4"}}]
                        }
                    },
                ]
            }
        
    }

    ret = qed.build("((f1=v1) and ((f2=v2) or (f2=v22))) or ((f3=v3) and (f4=v4))")
    assert ret == {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "filter": [
                                {"term": {"f1": "v1"}},
                                {
                                    "bool": {
                                        "should": [
                                            {"term": {"f2": "v2"}},
                                            {"term": {"f2": "v22"}},
                                        ]
                                    }
                                },
                            ]
                        }
                    },
                    {
                        "bool": {
                            "filter": [{"term": {"f3": "v3"}}, {"term": {"f4": "v4"}}]
                        }
                    },
                ]
            }
        
    }

    ret = qed.build(
        "((f1=v1) and ((f2=v2) or (f2=v22))) or ((f3=v3) and ((f4=v4) or (f4=v44)))"
    )
    assert ret == {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "filter": [
                                {"term": {"f1": "v1"}},
                                {
                                    "bool": {
                                        "should": [
                                            {"term": {"f2": "v2"}},
                                            {"term": {"f2": "v22"}},
                                        ]
                                    }
                                },
                            ]
                        }
                    },
                    {
                        "bool": {
                            "filter": [
                                {"term": {"f3": "v3"}},
                                {
                                    "bool": {
                                        "should": [
                                            {"term": {"f4": "v4"}},
                                            {"term": {"f4": "v44"}},
                                        ]
                                    }
                                },
                            ]
                        }
                    },
                ]
            }
    }

    ret = qed.build(
        "(name=vcp) and (((components.type=ocp) and (components.version=4.14.27)) and ((components.type=aspenmesh) and (components.version=1.18.7-am1)))"
    )
    assert ret == {
            "bool": {
                "filter": [
                    {"term": {"name": "vcp"}},
                    {
                        "bool": {
                            "filter": [
                                {
                                    "nested": {
                                        "path": "components",
                                        "query": {
                                            "bool": {
                                                "filter": [
                                                    {
                                                        "term": {
                                                            "components.type": "ocp"
                                                        }
                                                    },
                                                    {
                                                        "term": {
                                                            "components.version": "4.14.27"
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "components",
                                        "query": {
                                            "bool": {
                                                "filter": [
                                                    {
                                                        "term": {
                                                            "components.type": "aspenmesh"
                                                        }
                                                    },
                                                    {
                                                        "term": {
                                                            "components.version": "1.18.7-am1"
                                                        }
                                                    },
                                                ]
                                            }
                                        },
                                    }
                                },
                            ]
                        }
                    },
                ]
            }
    }

    ret = qed.build(
        "((components.type=cnf-certification-test)) and ((team.name not_in [telcoci, RedHat]))"
    )
    assert ret == {
            "bool": {
                "filter": [
                    {
                        "nested": {
                            "path": "components",
                            "query": {
                                "term": {"components.type": "cnf-certification-test"}
                            },
                        }
                    },
                    {
                        "nested": {
                            "path": "team",
                            "query": {
                                "bool": {
                                    "must_not": {
                                        "terms": {"team.name": ["telcoci", "RedHat"]}
                                    }
                                }
                            },
                        }
                    },
                ]
            }
    }


def test_query_1():
    ret = qed.build(
        "(components.type=cnf-certification-test) and (components.name not_in [telcoci, RedHat])"
    )
    assert ret == {
            "nested": {
                "path": "components",
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"components.type": "cnf-certification-test"}},
                            {
                                "bool": {
                                    "must_not": {
                                        "terms": {
                                            "components.name": ["telcoci", "RedHat"]
                                        }
                                    }
                                }
                            },
                        ]
                    }
                },
            }
    }


def test_query_2():

    ret = qed.build("components.type=cpt_type")
    assert ret == {
            "nested": {
                "path": "components",
                "query": {"term": {"components.type": "cpt_type"}},
            }
    }


def test_query_build_regex():
    ret = qed.build("(((components.name=openshift-vanilla) and (components.type=ocp)) and ((components.type=netapp-trident) and (components.version=~v24\\.02.*)))")
    assert ret == {'bool': {'filter': [{'nested': {'path': 'components',
                                 'query': {'bool': {'filter': [{'term': {'components.name': 'openshift-vanilla'}},
                                                               {'term': {'components.type': 'ocp'}}]}}}},
                     {'nested': {'path': 'components',
                                 'query': {'bool': {'filter': [{'term': {'components.type': 'netapp-trident'}},
                                                               {'regexp': {'components.version': {'case_insensitive': True,
                                                                                                  'flags': 'ALL',
                                                                                                  'value': 'v24\\.02.*'}}}]}}}}]}}
