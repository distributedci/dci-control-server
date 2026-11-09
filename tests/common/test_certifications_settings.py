import os
from pathlib import Path
import runpy

import mock
import pytest


@pytest.mark.parametrize(
    ("environment", "expected_container"),
    [
        ({}, "dci-certifications"),
        (
            {"STORE_CERTIFICATIONS_CONTAINER": "custom-certifications"},
            "custom-certifications",
        ),
    ],
)
def test_default_and_overridden_container(environment, expected_container):
    settings_file = Path(__file__).resolve().parents[2] / "dci" / "settings.py"
    with mock.patch.dict(os.environ, environment, clear=True):
        settings = runpy.run_path(str(settings_file))
    assert settings["STORE_CERTIFICATIONS_CONTAINER"] == expected_container
