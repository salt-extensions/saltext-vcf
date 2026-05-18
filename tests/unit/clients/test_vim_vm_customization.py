"""Tests for clients.vim_vm_customization (Linux/Windows spec builders + apply)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_customization

# ---------- linux_spec ----------


def test_linux_spec_dhcp_nic():
    spec = vim_vm_customization.linux_spec(
        "web-01",
        "example.com",
        nics=[{"dhcp": True}],
        dns_servers=["10.0.0.53"],
    )
    assert isinstance(spec, vim.vm.customization.Specification)
    assert isinstance(spec.identity, vim.vm.customization.LinuxPrep)
    assert spec.identity.hostName.name == "web-01"
    assert spec.identity.domain == "example.com"
    assert spec.globalIPSettings.dnsServerList == ["10.0.0.53"]
    assert len(spec.nicSettingMap) == 1
    assert isinstance(spec.nicSettingMap[0].adapter.ip, vim.vm.customization.DhcpIpGenerator)


def test_linux_spec_static_ip():
    spec = vim_vm_customization.linux_spec(
        "db-01",
        "example.com",
        nics=[
            {
                "ip": "10.0.0.5",
                "subnet": "255.255.255.0",
                "gateway": ["10.0.0.1"],
                "dns_servers": ["10.0.0.53"],
            }
        ],
    )
    ip = spec.nicSettingMap[0].adapter
    assert isinstance(ip.ip, vim.vm.customization.FixedIp)
    assert ip.ip.ipAddress == "10.0.0.5"
    assert ip.subnetMask == "255.255.255.0"
    assert ip.gateway == ["10.0.0.1"]


def test_linux_spec_invalid_nic_raises():
    with pytest.raises(ValueError, match="dhcp.*ip"):
        vim_vm_customization.linux_spec("h", "d", nics=[{}])


def test_linux_spec_time_zone_passed_through():
    spec = vim_vm_customization.linux_spec(
        "h", "d", time_zone="America/Los_Angeles", hw_clock_utc=False
    )
    assert spec.identity.timeZone == "America/Los_Angeles"
    assert spec.identity.hwClockUTC is False


# ---------- windows_spec ----------


def test_windows_spec_workgroup_default():
    spec = vim_vm_customization.windows_spec("WIN-01", "WORKGROUP", admin_password="P@ssw0rd")
    assert isinstance(spec.identity, vim.vm.customization.Sysprep)
    assert spec.identity.guiUnattended.password.value == "P@ssw0rd"
    assert spec.identity.guiUnattended.password.plainText is True
    assert spec.identity.identification.joinWorkgroup == "WORKGROUP"
    assert spec.identity.identification.joinDomain is None
    assert spec.identity.userData.computerName.name == "WIN-01"


def test_windows_spec_domain_join():
    spec = vim_vm_customization.windows_spec(
        "WIN-01",
        "example.com",
        domain_join=True,
        domain_admin="admin",
        domain_admin_password="secret",
    )
    assert spec.identity.identification.joinDomain == "example.com"
    assert spec.identity.identification.domainAdmin == "admin"
    assert spec.identity.identification.domainAdminPassword.value == "secret"


def test_windows_spec_time_zone_passed():
    spec = vim_vm_customization.windows_spec("h", "WG", time_zone=4)
    assert spec.identity.guiUnattended.timeZone == 4


# ---------- apply ----------


def test_apply_calls_customize_vm_task(monkeypatch, opts):
    from saltext.vcf.clients import vim_vm

    vm = MagicMock()
    vm.CustomizeVM_Task.return_value = MagicMock(_moId="task-cust-1")
    monkeypatch.setattr(vim_vm, "_vm", lambda o, v, profile=None: vm)
    spec = vim_vm_customization.linux_spec("h", "d", nics=[{"dhcp": True}])
    task_id = vim_vm_customization.apply(opts, "vm-100", spec)
    assert task_id == "task-cust-1"
    vm.CustomizeVM_Task.assert_called_once_with(spec=spec)


# ---------- spec management ----------


def test_spec_list(monkeypatch, opts):
    mod = vim_vm_customization

    info = [MagicMock(name="info1"), MagicMock(name="info2")]
    info[0].name = "linux-prod"
    info[1].name = "windows-prod"
    mgr = MagicMock()
    mgr.info = info
    monkeypatch.setattr(mod, "_csmgr", lambda o, profile=None: mgr)
    assert vim_vm_customization.spec_list(opts) == ["linux-prod", "windows-prod"]


def test_spec_delete(monkeypatch, opts):
    mod = vim_vm_customization

    mgr = MagicMock()
    monkeypatch.setattr(mod, "_csmgr", lambda o, profile=None: mgr)
    vim_vm_customization.spec_delete(opts, "linux-prod")
    mgr.DeleteCustomizationSpec.assert_called_once_with(name="linux-prod")
