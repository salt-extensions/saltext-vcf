"""Tests for modules.vcf_vcenter_host."""

import pytest
import responses

from saltext.vcf.modules import vcf_vcenter_host as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/host",
        json=[{"host": "h1"}],
        status=200,
    )
    assert mod.list_() == [{"host": "h1"}]


def test_get(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/host/h1",
        json={"name": "esxi01"},
        status=200,
    )
    assert mod.get("h1") == {"name": "esxi01"}


def test_enter_maintenance(vcenter_authed):
    vcenter_authed.add(responses.POST, "https://vc.test/api/vcenter/host/h1", status=204)
    mod.enter_maintenance("h1")
    call = vcenter_authed.calls[-1].request
    assert "action=enter-maintenance-mode" in call.url


def test_exit_maintenance(vcenter_authed):
    vcenter_authed.add(responses.POST, "https://vc.test/api/vcenter/host/h1", status=204)
    mod.exit_maintenance("h1")
    call = vcenter_authed.calls[-1].request
    assert "action=exit-maintenance-mode" in call.url
