"""Tests for modules.vcf_installer_appliance."""

import pytest

from saltext.vcf.clients import installer_appliance as c
from saltext.vcf.modules import vcf_installer_appliance as m


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
    monkeypatch.setattr(m, "__opts__", opts, raising=False)


def test_is_reachable_delegates(monkeypatch):
    monkeypatch.setattr(c, "is_appliance_reachable", lambda h, *, port, timeout: (h, port, timeout))
    assert m.is_reachable("h", 8443, 7) == ("h", 8443, 7)


def test_wait_until_reachable_returns_true(monkeypatch):
    called = {}

    def fake_wait(host, *, port, timeout, poll_interval):
        called.update(host=host, port=port, timeout=timeout, poll_interval=poll_interval)

    monkeypatch.setattr(c, "wait_until_reachable", fake_wait)
    assert m.wait_until_reachable("h", port=8443, timeout=10, poll_interval=2) is True
    assert called == {"host": "h", "port": 8443, "timeout": 10, "poll_interval": 2}


def test_deploy_reads_pillar_when_no_spec(monkeypatch):
    seen = {}

    def fake(spec):
        seen.update(spec)
        return {"vm_name": "vcf-installer", "vm_moid": "vm-1"}

    monkeypatch.setattr(c, "deploy_installer", fake)
    result = m.deploy()
    assert result["vm_moid"] == "vm-1"
    assert seen["installer_host"] == "installer.lab"


def test_deploy_uses_explicit_spec_over_pillar(monkeypatch):
    seen = {}
    monkeypatch.setattr(c, "deploy_installer", lambda s: seen.update(s) or {"vm_moid": "vm-9"})
    explicit = {
        "installer_host": "other",
        "installer_ova_url": "x",
        "installer_vm_name": "n",
        "installer_deploy_esxi": "e",
        "esxi_hosts": [],
    }
    m.deploy(installer_spec=explicit)
    assert seen["installer_host"] == "other"


def test_ensure_running_noop_when_already_reachable(monkeypatch):
    monkeypatch.setattr(c, "is_appliance_reachable", lambda *a, **kw: True)
    monkeypatch.setattr(c, "deploy_installer", lambda *_a, **_kw: pytest.fail("should not deploy"))
    assert m.ensure_running() == {"reachable": True, "deployed": False}


def test_ensure_running_deploys_and_waits(monkeypatch):
    monkeypatch.setattr(c, "is_appliance_reachable", lambda *a, **kw: False)
    monkeypatch.setattr(
        c, "deploy_installer", lambda spec: {"vm_name": "vcf-installer", "vm_moid": "vm-2"}
    )
    waits = []
    monkeypatch.setattr(
        c,
        "wait_until_reachable",
        lambda host, **kw: waits.append((host, kw)),
    )
    out = m.ensure_running()
    assert out == {
        "reachable": True,
        "deployed": True,
        "vm_name": "vcf-installer",
        "vm_moid": "vm-2",
    }
    assert waits[0][0] == "installer.lab"


def test_ensure_running_raises_when_no_pillar(monkeypatch, opts):
    opts["pillar"]["saltext.vcf"].pop("installer_appliance")
    with pytest.raises(KeyError, match="installer_appliance"):
        m.ensure_running()
