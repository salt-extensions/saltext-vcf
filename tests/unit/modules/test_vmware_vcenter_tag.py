"""Tests for modules.vmware_vcenter_tag."""

import json

import pytest
import responses

from saltext.vmware.modules import vmware_vcenter_tag as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/cis/tagging/tag",
        json=["urn:vmomi:Tag:1"],
        status=200,
    )
    assert mod.list_() == ["urn:vmomi:Tag:1"]


def test_create(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/cis/tagging/tag",
        json="urn:tag-1",
        status=200,
    )
    assert mod.create("env", "cat-1", description="environment") == "urn:tag-1"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["create_spec"]["name"] == "env"
    assert body["create_spec"]["category_id"] == "cat-1"


def test_delete(vcenter_authed):
    vcenter_authed.add(
        responses.DELETE, "https://vc.test/api/cis/tagging/tag/urn:tag-1", status=204
    )
    assert mod.delete("urn:tag-1") == {}


def test_assign(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/cis/tagging/tag-association/urn:tag-1",
        status=204,
    )
    mod.assign("urn:tag-1", "VirtualMachine", "vm-1")
    last = vcenter_authed.calls[-1].request
    assert "action=attach" in last.url


def test_list_assigned(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/cis/tagging/tag-association",
        json=["urn:tag-1"],
        status=200,
    )
    assert mod.list_assigned("VirtualMachine", "vm-1") == ["urn:tag-1"]
    assert "action=list-attached-tags" in vcenter_authed.calls[-1].request.url
