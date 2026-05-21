"""Tests for states.vcf_installer_appliance."""

import pytest

from saltext.vcf.modules import vcf_installer_appliance as m
from saltext.vcf.states import vcf_installer_appliance as st


@pytest.fixture(autouse=True)
def _inject_opts(monkeypatch, opts):
    opts["pillar"]["saltext.vcf"]["installer_appliance"] = {
        "installer_host": "installer.lab",
        "installer_port": 443,
        "installer_ova_url": "/tmp/installer.ova",
        "installer_vm_name": "vcf-installer",
        "installer_deploy_esxi": "esx-1.lab",
        "esxi_hosts": [{"fqdn": "esx-1.lab", "username": "root", "password": "p"}],
    }
    # __opts__ shared between module and state since state delegates to module helpers.
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    monkeypatch.setattr(m, "__opts__", opts, raising=False)


def test_running_noop_when_already_reachable(monkeypatch):
    monkeypatch.setattr(m, "is_reachable", lambda *a, **kw: True)
    monkeypatch.setattr(m, "ensure_running", lambda *_a, **_kw: pytest.fail("should not deploy"))
    ret = st.running("installer-up")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "already reachable" in ret["comment"]


def test_running_test_mode_when_not_reachable(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(m, "is_reachable", lambda *a, **kw: False)
    monkeypatch.setattr(m, "ensure_running", lambda *_a, **_kw: pytest.fail("should not deploy"))
    ret = st.running("installer-up")
    assert ret["result"] is None
    assert ret["changes"] == {"plan": "deploy_installer_ova", "target_host": "installer.lab"}
    assert "would deploy" in ret["comment"]


def test_running_deploys_when_not_reachable(monkeypatch):
    monkeypatch.setattr(m, "is_reachable", lambda *a, **kw: False)
    monkeypatch.setattr(
        m,
        "ensure_running",
        lambda _spec: {
            "reachable": True,
            "deployed": True,
            "vm_name": "vcf-installer",
            "vm_moid": "vm-42",
            "powered_on": True,
            "elapsed_sec": 12.3,
        },
    )
    ret = st.running("installer-up")
    assert ret["result"] is True
    assert ret["changes"]["deployed"] is True
    assert ret["changes"]["vm_moid"] == "vm-42"
    assert ret["changes"]["powered_on"] is True


def test_running_reports_failure(monkeypatch):
    monkeypatch.setattr(m, "is_reachable", lambda *a, **kw: False)

    def boom(_spec):
        raise RuntimeError("ovftool not on PATH")

    monkeypatch.setattr(m, "ensure_running", boom)
    ret = st.running("installer-up")
    assert ret["result"] is False
    assert "ovftool not on PATH" in ret["comment"]


def test_running_passes_explicit_spec(monkeypatch):
    monkeypatch.setattr(m, "is_reachable", lambda *a, **kw: True)
    explicit = {
        "installer_host": "other.lab",
        "installer_port": 8443,
        "installer_ova_url": "x",
        "installer_vm_name": "n",
        "installer_deploy_esxi": "e",
        "esxi_hosts": [],
    }
    ret = st.running("installer-up", installer_spec=explicit)
    assert ret["result"] is True
    assert "other.lab:8443" in ret["comment"]
