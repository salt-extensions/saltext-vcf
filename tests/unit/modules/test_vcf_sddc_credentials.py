"""Tests for modules.vcf_sddc_credentials."""

import json

import pytest
import responses

from saltext.vcf.modules import vcf_sddc_credentials as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/credentials",
        json={"elements": []},
        status=200,
    )
    assert mod.list_() == {"elements": []}


def test_rotate_builds_patch_body(sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        "https://sm.test/v1/credentials",
        json={"id": "task-1"},
        status=202,
    )
    elements = [{"resourceName": "esxi01", "resourceType": "ESXI"}]
    assert mod.rotate(elements) == {"id": "task-1"}
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"operationType": "ROTATE", "elements": elements}
