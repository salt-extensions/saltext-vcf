"""Tests for the final mid/low-impact gap clients.

Covers vim_host_certificate, vim_infra_profile, vim_vasa, vim_vm_devices,
vim_vm_console, and the new methods on vim_vm + vim_host_network +
vim_vm_tools.
"""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_host_certificate
from saltext.vcf.clients import vim_host_network
from saltext.vcf.clients import vim_infra_profile
from saltext.vcf.clients import vim_vasa
from saltext.vcf.clients import vim_vm
from saltext.vcf.clients import vim_vm_console
from saltext.vcf.clients import vim_vm_devices

# ---------------------------------------------------------------------------
# Host certificate
# ---------------------------------------------------------------------------


@pytest.fixture
def cert_host(monkeypatch):
    host = MagicMock()
    host.config.certificate = b"-----BEGIN CERT-----\nMIIB...\n-----END CERT-----\n"
    host.runtime.certificateInfo.issuer = "CN=VMCA"
    host.runtime.certificateInfo.subject = "CN=esx-1"
    host.runtime.certificateInfo.status = "valid"
    host.runtime.certificateInfo.notBefore.isoformat = lambda: "2026-01-01T00:00:00+00:00"
    host.runtime.certificateInfo.notAfter.isoformat = lambda: "2027-01-01T00:00:00+00:00"
    cm = host.configManager.certificateManager
    cm.GenerateCertificateSigningRequest.return_value = "-----BEGIN CSR-----..."
    monkeypatch.setattr(vim_host_certificate, "_host", lambda o, n, profile=None: host)
    return {"host": host, "cm": cm}


def test_certificate_info(opts, cert_host):
    out = vim_host_certificate.info(opts, "esx-1")
    assert out["issuer"] == "CN=VMCA"
    assert out["subject"] == "CN=esx-1"
    assert "BEGIN CERT" in out["pem"]
    assert out["not_after"].startswith("2027")


def test_certificate_csr(opts, cert_host):
    csr = vim_host_certificate.generate_csr(opts, "esx-1")
    assert csr.startswith("-----BEGIN CSR")
    cert_host["cm"].GenerateCertificateSigningRequest.assert_called_with(
        useIpAddressAsCommonName=True
    )


def test_certificate_install(opts, cert_host):
    assert vim_host_certificate.install_cert(opts, "esx-1", "PEM") is True
    cert_host["cm"].InstallServerCertificate.assert_called_with(cert="PEM")


def test_certificate_refresh(opts, cert_host):
    vim_host_certificate.refresh_cert(opts, "esx-1")
    cert_host["cm"].RefreshCertificate.assert_called_once()


def test_certificate_refresh_ca(opts, cert_host):
    vim_host_certificate.refresh_ca_bundle(opts, "esx-1")
    cert_host["cm"].RefreshCACertificates.assert_called_once()


# ---------------------------------------------------------------------------
# Infra profile
# ---------------------------------------------------------------------------


def _make_host_profile(mo_id, name, description=""):
    p = MagicMock()
    p._moId = mo_id  # noqa: SLF001
    p.name = name
    p.config.annotation = description
    p.enabled = True
    p.complyStatus = "compliant"
    p.entity = []
    p.ExportProfile.return_value = "<xml>profile-xml</xml>"
    return p


@pytest.fixture
def profile_mgr(monkeypatch):
    mgr = MagicMock()
    mgr.profile = [_make_host_profile("hp-1", "gold-profile"), _make_host_profile("hp-2", "iron")]
    monkeypatch.setattr(vim_infra_profile, "_profile_mgr", lambda o, profile=None: mgr)
    return mgr


def test_infra_profile_list(opts, profile_mgr):
    out = vim_infra_profile.list_(opts)
    assert [p["name"] for p in out] == ["gold-profile", "iron"]


def test_infra_profile_get(opts, profile_mgr):
    out = vim_infra_profile.get(opts, "gold-profile")
    assert out["id"] == "hp-1"


def test_infra_profile_get_or_none(opts, profile_mgr):
    assert vim_infra_profile.get_or_none(opts, "missing") is None


def test_infra_profile_export(opts, profile_mgr):
    xml = vim_infra_profile.export(opts, "gold-profile")
    assert xml == "<xml>profile-xml</xml>"


# ---------------------------------------------------------------------------
# VASA
# ---------------------------------------------------------------------------


def test_vasa_list_returns_empty_when_no_endpoint(opts, monkeypatch):
    # SMS stub unavailable on the lab — _sms_stub raises and we return []
    def boom(opts, profile=None):
        raise RuntimeError("no SMS")

    monkeypatch.setattr(vim_vasa, "_sms_stub", boom)
    assert vim_vasa.list_(opts) == []


def test_vasa_get_or_none_missing(opts, monkeypatch):
    monkeypatch.setattr(vim_vasa, "list_", lambda o, profile=None: [])
    assert vim_vasa.get_or_none(opts, "anything") is None


# ---------------------------------------------------------------------------
# VM devices: vTPM, vGPU, serial, video
# ---------------------------------------------------------------------------


def _fake_vm_with_devices(devices=None):
    vm = MagicMock()
    vm.config.hardware.device = devices or []
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-dev")
    return vm


@pytest.fixture
def vm_factory(monkeypatch):
    holder = {"vm": _fake_vm_with_devices()}
    monkeypatch.setattr(vim_vm_devices, "_vm", lambda o, n, profile=None: holder["vm"])
    return holder


def test_tpm_add(opts, vm_factory):
    assert vim_vm_devices.tpm_add(opts, "myvm") == "task-dev"
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.deviceChange[0].operation == "add"
    assert isinstance(spec.deviceChange[0].device, vim.vm.device.VirtualTPM)


def test_tpm_list(opts, vm_factory):
    tpm = vim.vm.device.VirtualTPM()
    tpm.key = 12345
    desc = vim.Description()
    desc.label = "TPM 2.0"
    desc.summary = "TPM 2.0 device"
    tpm.deviceInfo = desc
    vm_factory["vm"].config.hardware.device = [tpm]
    out = vim_vm_devices.tpm_list(opts, "myvm")
    assert out[0]["key"] == 12345
    assert out[0]["label"] == "TPM 2.0"


def test_tpm_remove(opts, vm_factory):
    tpm = vim.vm.device.VirtualTPM()
    tpm.key = 5
    tpm.deviceInfo = vim.Description(label="TPM", summary="")
    vm_factory["vm"].config.hardware.device = [tpm]
    vim_vm_devices.tpm_remove(opts, "myvm")
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.deviceChange[0].operation == "remove"


def test_tpm_remove_missing(opts, vm_factory):
    with pytest.raises(LookupError):
        vim_vm_devices.tpm_remove(opts, "myvm")


def test_vgpu_add(opts, vm_factory):
    vim_vm_devices.vgpu_add(opts, "myvm", "grid_a100d-8c")
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    dev = spec.deviceChange[0].device
    assert isinstance(dev, vim.vm.device.VirtualPCIPassthrough)
    assert isinstance(dev.backing, vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo)
    assert dev.backing.vgpu == "grid_a100d-8c"


def test_vgpu_list(opts, vm_factory):
    dev = vim.vm.device.VirtualPCIPassthrough()
    dev.key = 7
    dev.deviceInfo = vim.Description(label="vgpu", summary="")
    backing = vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo()
    backing.vgpu = "grid_v100-4c"
    dev.backing = backing
    vm_factory["vm"].config.hardware.device = [dev]
    out = vim_vm_devices.vgpu_list(opts, "myvm")
    assert out[0]["vgpu_profile"] == "grid_v100-4c"


def test_video_get_returns_none_when_no_video(opts, vm_factory):
    assert vim_vm_devices.video_get(opts, "myvm") is None


def test_video_update_changes_num_displays(opts, vm_factory):
    card = vim.vm.device.VirtualVideoCard()
    card.key = 500
    card.videoRamSizeInKB = 4096
    card.numDisplays = 1
    card.useAutoDetect = True
    card.enable3DSupport = False
    card.graphicsMemorySizeInKB = 0
    card.deviceInfo = vim.Description(label="video card", summary="")
    vm_factory["vm"].config.hardware.device = [card]
    vim_vm_devices.video_update(opts, "myvm", num_displays=2)
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.deviceChange[0].operation == "edit"
    assert spec.deviceChange[0].device.numDisplays == 2


def test_serial_add_network_backing(opts, vm_factory):
    vim_vm_devices.serial_add(opts, "myvm", backing="network", uri="tcp://0.0.0.0:9000")
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    port = spec.deviceChange[0].device
    assert isinstance(port, vim.vm.device.VirtualSerialPort)
    assert isinstance(port.backing, vim.vm.device.VirtualSerialPort.URIBackingInfo)
    assert port.backing.serviceURI == "tcp://0.0.0.0:9000"


def test_serial_add_file_backing(opts, vm_factory):
    vim_vm_devices.serial_add(opts, "myvm", backing="file", file_path="[ds1] serial.log")
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    port = spec.deviceChange[0].device
    assert isinstance(port.backing, vim.vm.device.VirtualSerialPort.FileBackingInfo)


def test_serial_add_requires_uri(opts, vm_factory):
    with pytest.raises(ValueError, match="uri"):
        vim_vm_devices.serial_add(opts, "myvm", backing="network")


def test_serial_remove(opts, vm_factory):
    port = vim.vm.device.VirtualSerialPort()
    port.key = 1234
    port.backing = vim.vm.device.VirtualSerialPort.URIBackingInfo()
    port.backing.serviceURI = "tcp://x"
    port.deviceInfo = vim.Description(label="serial", summary="")
    vm_factory["vm"].config.hardware.device = [port]
    vim_vm_devices.serial_remove(opts, "myvm")
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.deviceChange[0].operation == "remove"


# ---------------------------------------------------------------------------
# VM console
# ---------------------------------------------------------------------------


@pytest.fixture
def console_vm_factory(monkeypatch):
    vm = MagicMock()
    vm.CreateScreenshot_Task.return_value = MagicMock(_moId="task-shot")
    vm.PutUsbScanCodes.return_value = 3
    monkeypatch.setattr(vim_vm_console, "_vm", lambda o, n, profile=None: vm)
    return vm


def test_screenshot(opts, console_vm_factory):
    assert vim_vm_console.screenshot(opts, "myvm") == "task-shot"


def test_send_keys_by_name(opts, console_vm_factory):
    out = vim_vm_console.send_keys(opts, "myvm", ["enter", "f2", "a"])
    assert out == 3
    spec = console_vm_factory.PutUsbScanCodes.call_args.kwargs["spec"]
    assert len(spec.keyEvents) == 3


def test_send_keys_unknown_raises(opts, console_vm_factory):
    with pytest.raises(ValueError, match="unknown key"):
        vim_vm_console.send_keys(opts, "myvm", ["NotARealKey"])


# ---------------------------------------------------------------------------
# vim_vm extensions
# ---------------------------------------------------------------------------


@pytest.fixture
def vm_lookup(monkeypatch):
    src = MagicMock()
    src._moId = "vm-src"  # noqa: SLF001
    src.name = "source"
    src.InstantClone_Task.return_value = MagicMock(_moId="task-ic")
    src.UnregisterVM.return_value = None
    folder = vim.Folder("folder-1", None)
    monkeypatch.setattr(vim_vm, "_vm", lambda o, n, profile=None: src)
    monkeypatch.setattr(
        vim_vm,
        "_find_by_type",
        lambda o, t, n, profile=None: folder if t is vim.Folder else MagicMock(),
    )
    return {"src": src, "folder": folder}


def test_instant_clone(opts, vm_lookup):
    assert vim_vm.instant_clone(opts, "source", "new-vm") == "task-ic"
    spec = vm_lookup["src"].InstantClone_Task.call_args.kwargs["spec"]
    assert spec.name == "new-vm"


def test_instant_clone_with_extra_config(opts, vm_lookup):
    vim_vm.instant_clone(opts, "source", "new-vm", extra_config={"guestinfo.role": "worker"})
    spec = vm_lookup["src"].InstantClone_Task.call_args.kwargs["spec"]
    assert spec.config[0].key == "guestinfo.role"
    assert spec.config[0].value == "worker"


def test_move_to_folder(opts, vm_lookup, monkeypatch):
    target_folder = MagicMock()
    target_folder.MoveIntoFolder_Task.return_value = MagicMock(_moId="task-mv")
    monkeypatch.setattr(vim_vm, "_find_by_type", lambda o, t, n, profile=None: target_folder)
    assert vim_vm.move_to_folder(opts, "source", "myfolder") == "task-mv"
    target_folder.MoveIntoFolder_Task.assert_called_once()


def test_unregister(opts, vm_lookup):
    assert vim_vm.unregister(opts, "source") is True
    vm_lookup["src"].UnregisterVM.assert_called_once()


# ---------------------------------------------------------------------------
# vim_host_network IPv6 + vmkernel_migrate
# ---------------------------------------------------------------------------


def test_ipv6_get_true(opts, monkeypatch):
    host = MagicMock()
    host.config.network.ipV6Enabled = True
    monkeypatch.setattr(vim_host_network, "_host", lambda o, n, profile=None: host)
    assert vim_host_network.ipv6_get(opts, "esx-1") == {"enabled": True}


def test_ipv6_set_false(opts, monkeypatch):
    net = MagicMock()
    monkeypatch.setattr(vim_host_network, "_net", lambda o, n, profile=None: net)
    host = MagicMock()
    host.config.network.ipV6Enabled = False
    monkeypatch.setattr(vim_host_network, "_host", lambda o, n, profile=None: host)
    out = vim_host_network.ipv6_set(opts, "esx-1", False)
    assert out == {"enabled": False}
    spec = net.UpdateNetworkConfig.call_args.kwargs["config"]
    assert spec.ipV6Enabled is False


def test_vmkernel_migrate(opts, monkeypatch):
    state = {
        "existing": {
            "device": "vmk2",
            "portgroup": "old-pg",
            "ip_address": "10.0.0.5",
            "subnet_mask": "255.255.255.0",
            "mtu": 9000,
            "dhcp": False,
            "mac_address": None,
        }
    }
    monkeypatch.setattr(
        vim_host_network, "vmkernel_get", lambda o, h, d, profile=None: state["existing"]
    )
    monkeypatch.setattr(
        vim_host_network, "vmkernel_remove", lambda o, h, d, profile=None: state.update(removed=d)
    )
    monkeypatch.setattr(
        vim_host_network,
        "vmkernel_add",
        lambda o, h, p, **kw: state.update(added=p, kw=kw) or "vmk3",
    )
    out = vim_host_network.vmkernel_migrate(opts, "esx-1", "vmk2", "new-pg")
    assert out == "vmk3"
    assert state["removed"] == "vmk2"
    assert state["added"] == "new-pg"
    assert state["kw"]["ip_address"] == "10.0.0.5"
    assert state["kw"]["mtu"] == 9000
