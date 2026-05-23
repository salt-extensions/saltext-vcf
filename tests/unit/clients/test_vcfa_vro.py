"""Tests for the vRO-rooted vcfa_* clients."""

import json

import responses

from saltext.vcf.clients import vcfa_vro_config_element
from saltext.vcf.clients import vcfa_vro_package
from saltext.vcf.clients import vcfa_workflow_run

# -- vro_package --------------------------------------------------------


def test_package_import_uses_multipart(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/vco/api/packages",
        json={"name": "com.example"},
        status=200,
    )
    out = vcfa_vro_package.import_(opts, "com.example", b"contents")
    assert out == {"name": "com.example"}
    req = vcfa_authed.calls[-1].request
    assert "multipart/form-data" in req.headers.get("Content-Type", "")


def test_package_delete_sends_option(opts, vcfa_authed):
    vcfa_authed.add(responses.DELETE, "https://vcfa.test/vco/api/packages/com.example", status=204)
    vcfa_vro_package.delete(opts, "com.example", option="deletePackageWithContent")
    assert "option=deletePackageWithContent" in vcfa_authed.calls[-1].request.url


def test_package_export_returns_raw_bytes(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/vco/api/packages/com.example",
        body=b"package-bytes",
        status=200,
        content_type="application/octet-stream",
    )
    assert vcfa_vro_package.export_(opts, "com.example") == b"package-bytes"


# -- vro_config_element -----------------------------------------------


def test_config_element_list_with_category(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/vco/api/configurations",
        json={"content": []},
        status=200,
    )
    vcfa_vro_config_element.list_(opts, category="cat-1")
    assert "categoryId=cat-1" in vcfa_authed.calls[-1].request.url


def test_config_element_set_attribute(opts, vcfa_authed):
    vcfa_authed.add(
        responses.PUT,
        "https://vcfa.test/vco/api/configurations/cfg-1/attributes/foo",
        json={},
        status=200,
    )
    vcfa_vro_config_element.set_attribute(
        opts, "cfg-1", "foo", {"name": "foo", "type": "string", "value": "bar"}
    )
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"name": "foo", "type": "string", "value": "bar"}


# -- workflow_run -------------------------------------------------------


def test_workflow_run_start(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/vco/api/workflows/wf-1/executions",
        json={"id": "run-1"},
        status=200,
    )
    out = vcfa_workflow_run.start(
        opts, "wf-1", parameters=[{"name": "x", "type": "string", "value": "y"}]
    )
    assert out == {"id": "run-1"}
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"parameters": [{"name": "x", "type": "string", "value": "y"}]}


def test_workflow_run_cancel(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/vco/api/workflows/wf-1/executions/run-1/state",
        json={},
        status=200,
    )
    vcfa_workflow_run.cancel(opts, "wf-1", "run-1")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"value": "canceled"}


def test_workflow_run_state(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/vco/api/workflows/wf-1/executions/run-1/state",
        json={"value": "completed"},
        status=200,
    )
    assert vcfa_workflow_run.state(opts, "wf-1", "run-1") == {"value": "completed"}
