"""Tests for clients.vcfops_adapter (kinds + instances)."""

import pytest
import requests
import responses

from saltext.vcf.clients import vcfops_adapter as ca

_KINDS = "https://ops.test/suite-api/api/adapterkinds"
_INSTANCES = "https://ops.test/suite-api/api/adapters"


def test_kinds_list(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _KINDS, json={"adapter-kind": []}, status=200)
    assert ca.list_(opts) == {"adapter-kind": []}


def test_kinds_get(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_KINDS}/VMWARE", json={"key": "VMWARE"}, status=200)
    assert ca.get(opts, "VMWARE")["key"] == "VMWARE"


def test_kinds_get_or_none_returns_none_on_404(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_KINDS}/missing", status=404)
    assert ca.get_or_none(opts, "missing") is None


def test_kinds_get_or_none_propagates_non_404(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_KINDS}/boom", status=500)
    with pytest.raises(requests.HTTPError):
        ca.get_or_none(opts, "boom")


def test_instance_list_happy_path(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        _INSTANCES,
        json={"adapterInstancesInfoDto": [{"id": "a-1"}, {"id": "a-2"}]},
        status=200,
    )
    out = ca.instance_list(opts)
    assert [a["id"] for a in out["adapterInstancesInfoDto"]] == ["a-1", "a-2"]


def test_instance_get_happy_path(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_INSTANCES}/a-1",
        json={"id": "a-1", "resourceKey": {"name": "vc-prod"}},
        status=200,
    )
    assert ca.instance_get(opts, "a-1")["id"] == "a-1"


def test_instance_get_or_none_returns_none_on_404(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_INSTANCES}/missing", status=404)
    assert ca.instance_get_or_none(opts, "missing") is None


def test_instance_get_or_none_propagates_non_404(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_INSTANCES}/boom", status=500)
    with pytest.raises(requests.HTTPError):
        ca.instance_get_or_none(opts, "boom")


def test_instance_create_posts_spec(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        _INSTANCES,
        json={"id": "new-adapter"},
        status=201,
    )
    spec = {
        "name": "vcenter-prod",
        "adapterKindKey": "VMWARE",
        "credentialInstanceId": "cred-1",
    }
    out = ca.instance_create(opts, spec)
    assert out == {"id": "new-adapter"}
    call = vcfops_authed.calls[-1]
    assert call.request.method == "POST"
    assert call.request.url.endswith("/suite-api/api/adapters")


def test_instance_update_puts_spec(opts, vcfops_authed):
    vcfops_authed.add(
        responses.PUT,
        f"{_INSTANCES}/a-1",
        json={"id": "a-1"},
        status=200,
    )
    ca.instance_update(opts, "a-1", {"name": "renamed"})
    call = vcfops_authed.calls[-1]
    assert call.request.method == "PUT"
    assert call.request.url.endswith("/suite-api/api/adapters/a-1")


def test_instance_delete(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_INSTANCES}/a-1", status=204)
    ca.instance_delete(opts, "a-1")
    call = vcfops_authed.calls[-1]
    assert call.request.method == "DELETE"
    assert call.request.url.endswith("/suite-api/api/adapters/a-1")


def test_instance_start_posts_to_start_path(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_INSTANCES}/a-1/monitoringstate/start",
        status=200,
    )
    ca.instance_start(opts, "a-1")
    call = vcfops_authed.calls[-1]
    assert call.request.method == "POST"
    assert call.request.url.endswith("/suite-api/api/adapters/a-1/monitoringstate/start")


def test_instance_stop_posts_to_stop_path(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_INSTANCES}/a-1/monitoringstate/stop",
        status=200,
    )
    ca.instance_stop(opts, "a-1")
    call = vcfops_authed.calls[-1]
    assert call.request.method == "POST"
    assert call.request.url.endswith("/suite-api/api/adapters/a-1/monitoringstate/stop")
