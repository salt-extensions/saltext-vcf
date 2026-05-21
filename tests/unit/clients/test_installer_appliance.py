"""Tests for clients.installer_appliance (TCP probe + deploy facade)."""

from unittest import mock

import pytest

from saltext.vcf.clients import installer_appliance


def test_is_appliance_reachable_true(monkeypatch):
    monkeypatch.setattr(
        installer_appliance.socket,
        "create_connection",
        lambda *_a, **_kw: mock.MagicMock(__enter__=lambda s: s, __exit__=lambda *a: None),
    )
    assert installer_appliance.is_appliance_reachable("installer.test") is True


def test_is_appliance_reachable_connection_refused(monkeypatch):
    def boom(*_a, **_kw):
        raise ConnectionRefusedError

    monkeypatch.setattr(installer_appliance.socket, "create_connection", boom)
    assert installer_appliance.is_appliance_reachable("installer.test") is False


def test_is_appliance_reachable_timeout(monkeypatch):
    def boom(*_a, **_kw):
        raise TimeoutError

    monkeypatch.setattr(installer_appliance.socket, "create_connection", boom)
    assert installer_appliance.is_appliance_reachable("installer.test") is False


def test_wait_until_reachable_returns_when_ready(monkeypatch):
    calls = {"n": 0}

    def fake_reachable(host, *, port=443, timeout=5):
        calls["n"] += 1
        return calls["n"] >= 3

    sleeps = []
    monkeypatch.setattr(installer_appliance, "is_appliance_reachable", fake_reachable)
    monkeypatch.setattr(installer_appliance.time, "monotonic", lambda: 0)
    monkeypatch.setattr(installer_appliance.time, "sleep", sleeps.append)

    installer_appliance.wait_until_reachable("h", poll_interval=1, timeout=60)
    assert calls["n"] == 3
    assert sleeps == [1, 1]


def test_wait_until_reachable_raises_on_timeout(monkeypatch):
    monkeypatch.setattr(installer_appliance, "is_appliance_reachable", lambda *_a, **_kw: False)
    monkeypatch.setattr(installer_appliance.time, "sleep", lambda _s: None)

    # Time stepper: 0, 0, 100 (past deadline=60).
    seq = iter([0.0, 0.0, 100.0])
    monkeypatch.setattr(installer_appliance.time, "monotonic", lambda: next(seq))

    with pytest.raises(TimeoutError):
        installer_appliance.wait_until_reachable("h", poll_interval=1, timeout=60)


def test_deploy_installer_picks_credentials_for_target(monkeypatch):
    spec = {
        "installer_ova_url": "/tmp/installer.ova",
        "installer_vm_name": "vcf-installer",
        "installer_deploy_esxi": "esx-1.lab.local",
        "esxi_hosts": [
            {"fqdn": "esx-0.lab.local", "username": "root", "password": "wrong"},
            {"fqdn": "esx-1.lab.local", "username": "root", "password": "right"},
        ],
        "network_map": {"VM Network": "VM Network"},
    }
    seen = {}

    def fake_deploy(**kwargs):
        seen.update(kwargs)
        return {"vm_name": "vcf-installer", "vm_moid": "vm-42"}

    monkeypatch.setattr(installer_appliance.ovf_deploy, "deploy_ova", fake_deploy)
    result = installer_appliance.deploy_installer(spec)
    assert result["vm_moid"] == "vm-42"
    assert seen["target_host"] == "esx-1.lab.local"
    assert seen["target_user"] == "root"
    assert seen["target_password"] == "right"
    assert seen["vm_name"] == "vcf-installer"
    assert seen["network_map"] == {"VM Network": "VM Network"}


def test_deploy_installer_raises_when_no_matching_host(monkeypatch):
    spec = {
        "installer_ova_url": "/tmp/installer.ova",
        "installer_vm_name": "vcf-installer",
        "installer_deploy_esxi": "esx-missing.lab.local",
        "esxi_hosts": [{"fqdn": "esx-0.lab.local", "username": "root", "password": "p"}],
    }
    monkeypatch.setattr(installer_appliance.ovf_deploy, "deploy_ova", lambda **kw: {})
    with pytest.raises(LookupError):
        installer_appliance.deploy_installer(spec)
