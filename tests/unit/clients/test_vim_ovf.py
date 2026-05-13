"""Tests for clients.vim_ovf (OVF descriptor + export via HttpNfcLease)."""

from unittest.mock import MagicMock

import pytest
import responses
from pyVmomi import vim

from saltext.vmware.clients import vim_ovf


@pytest.fixture
def vm_env(monkeypatch):
    vm = MagicMock()
    vm._moId = "vm-1"  # noqa: SLF001
    vm.name = "test-vm"

    monkeypatch.setattr(vim_ovf, "_find_vm", lambda opts, n, profile=None: vm)

    content = MagicMock()
    descriptor_result = MagicMock()
    descriptor_result.ovfDescriptor = "<Envelope/>"
    descriptor_result.warning = []
    content.ovfManager.CreateDescriptor.return_value = descriptor_result

    monkeypatch.setattr(
        "saltext.vmware.clients.vim_ovf.soap.content", lambda o, profile=None: content
    )
    return {"vm": vm, "content": content, "descriptor_result": descriptor_result}


def test_descriptor_returns_xml(opts, vm_env):
    out = vim_ovf.descriptor(opts, "test-vm")
    assert out["ovf"] == "<Envelope/>"
    assert out["warnings"] == []
    vm_env["content"].ovfManager.CreateDescriptor.assert_called_once()


def test_export_walks_lease_and_completes(opts, vm_env, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "saltext.vmware.clients.vim_ovf.vc_rest.get_config",
        lambda o, profile=None: {"host": "vc.test", "verify_ssl": False},
    )
    monkeypatch.setattr(
        "saltext.vmware.clients.vim_ovf.soap.session_cookie",
        lambda o, profile=None: "vmware_soap_session=token",
    )
    lease = MagicMock()
    lease.state = vim.HttpNfcLease.State.ready
    device = MagicMock()
    device.disk = True
    device.url = "https://vc.test/nfc/disk-1.vmdk"
    device.targetId = "disk-1"
    device.key = "key-1"
    lease.info.deviceUrl = [device]
    vm_env["vm"].ExportVm.return_value = lease
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            "https://vc.test/nfc/disk-1.vmdk",
            body=b"DISKBYTES",
            status=200,
        )
        out = vim_ovf.export(opts, "test-vm", str(tmp_path))
    assert (tmp_path / "test-vm.ovf").read_text() == "<Envelope/>"
    assert len(out["vmdk_paths"]) == 1
    lease.HttpNfcLeaseComplete.assert_called_once()
