"""Tests for modules.vcf_vcenter_datacenter."""

import pytest
import responses

from saltext.vcf.modules import vcf_vcenter_datacenter as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datacenter",
        json=[{"datacenter": "dc-1"}],
        status=200,
    )
    assert mod.list_() == [{"datacenter": "dc-1"}]


def test_get(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datacenter/dc-1",
        json={"name": "DC1"},
        status=200,
    )
    assert mod.get("dc-1") == {"name": "DC1"}


def test_create(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/datacenter",
        json="dc-new",
        status=200,
    )
    assert mod.create("DC1", folder="folder-1") == "dc-new"


def test_delete(vcenter_authed):
    vcenter_authed.add(responses.DELETE, "https://vc.test/api/vcenter/datacenter/dc-1", status=204)
    assert mod.delete("dc-1") == {}
