"""Tests for the vim_vm inventory additions (templates, path, info, bulk register/unregister)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm


def _fake_vm(name="web-01", moid="vm-100", template=False, power="poweredOff"):
    vm = MagicMock()
    vm._moId = moid  # noqa: SLF001
    vm.name = name
    vm.config.template = template
    vm.runtime.powerState = power
    vm.summary.runtime.powerState = power
    vm.summary.config.guestId = "rhel9_64Guest"
    vm.summary.config.uuid = "42012345-6789"
    vm.config.files.vmPathName = "[ds1] web-01/web-01.vmx"
    vm.config.annotation = ""
    vm.guest.net = []
    vm.datastore = []
    vm.UnregisterVM.return_value = None
    return vm


def _fake_content(root=None):
    content = MagicMock()
    container = MagicMock()
    content.viewManager.CreateContainerView.return_value = container
    container.view = []
    if root is not None:
        content.rootFolder = root
    return content


class _Node:
    def __init__(self, name, moid, parent=None):
        self.name = name
        self._moId = moid  # noqa: SLF001
        self.parent = parent


def test_list_templates_filters(opts):
    tmpl = _fake_vm(name="gold", moid="vm-1", template=True)
    plain = _fake_vm(name="web", moid="vm-2")
    content = _fake_content()
    content.viewManager.CreateContainerView.return_value.view = [tmpl, plain]
    with patch("saltext.vcf.utils.vim.content", return_value=content):
        assert vim_vm.list_templates(opts) == ["gold"]


def test_path_walks_parents(opts):
    root = MagicMock()
    root._moId = "root"  # noqa: SLF001
    dc = _Node("MyDC", "dc-1", parent=root)
    folder = _Node("vm", "group-1", parent=dc)
    vm = _Node("web-01", "vm-1", parent=folder)
    vm2 = _fake_vm()
    with (
        patch.object(vim_vm, "_vm", return_value=vm),
        patch("saltext.vcf.utils.vim.content", return_value=_fake_content(root=root)),
    ):
        assert vim_vm.path(opts, vm2) == "/MyDC/vm/web-01"


def test_runtime_shape(opts):
    host = MagicMock()
    host.name = "host-1"
    ds = MagicMock()
    ds.name = "ds1"
    vm = _fake_vm()
    vm.runtime.host = host
    vm.datastore = [ds]
    with patch.object(vim_vm, "_vm", return_value=vm):
        assert vim_vm.runtime(opts, "web-01") == {"host": "host-1", "datastores": ["ds1"]}


def test_info_shape(opts):
    vm = _fake_vm()
    vm.parent = None
    net = MagicMock()
    net.ipAddress = ["10.0.0.5"]
    vm.guest.net = [net]
    nic = MagicMock(spec=vim.vm.device.VirtualEthernetCard)
    nic.macAddress = "00:50:56:aa:bb:cc"
    vm.config.hardware.device = [nic]
    root = MagicMock()
    root._moId = "root"  # noqa: SLF001
    with (
        patch.object(vim_vm, "_vm", return_value=vm),
        patch("saltext.vcf.utils.vim.content", return_value=_fake_content(root=root)),
    ):
        result = vim_vm.info(opts, "web-01")
    assert result["name"] == "web-01"
    assert result["ip_addresses"] == ["10.0.0.5"]
    assert result["mac_addresses"] == ["00:50:56:aa:bb:cc"]
    assert result["vm_path_name"] == "[ds1] web-01/web-01.vmx"
    assert result["template"] is False


def test_unregister_refuses_when_powered_on(opts):
    vm = _fake_vm(power="poweredOn")
    with patch.object(vim_vm, "_vm", return_value=vm):
        with pytest.raises(RuntimeError):
            vim_vm.unregister(opts, "web-01", shutdown=False)
    vm.UnregisterVM.assert_not_called()


def test_unregister_shutdown_powers_off_then_unregisters(opts):
    vm = _fake_vm(power="poweredOn")
    # Graceful path: after ShutdownGuest the powerState flips to poweredOff.
    def _flip():
        vm.runtime.powerState = "poweredOff"

    vm.ShutdownGuest.side_effect = _flip
    with (
        patch.object(vim_vm, "_vm", return_value=vm),
        patch.object(vim_vm.time, "sleep", return_value=None),
    ):
        assert vim_vm.unregister(opts, "web-01", shutdown=True) is True
    vm.ShutdownGuest.assert_called_once()
    vm.UnregisterVM.assert_called_once()


def test_unregister_all_batches(opts):
    vm1 = _fake_vm(name="a", moid="vm-1")
    vm2 = _fake_vm(name="b", moid="vm-2")
    folder = MagicMock()
    folder.childEntity = [vm1, vm2]
    with (
        patch.object(vim_vm, "_find_by_type", return_value=folder),
        patch("saltext.vcf.utils.vim.content", return_value=_fake_content()),
    ):
        result = vim_vm.unregister_all(opts, folder="restored", shutdown=True)
    assert result["a"]["success"] is True
    assert result["b"]["success"] is True
    assert vm1.UnregisterVM.called and vm2.UnregisterVM.called


def test_unregister_all_reports_failure(opts):
    ok = _fake_vm(name="a", moid="vm-1")
    bad = _fake_vm(name="b", moid="vm-2")
    bad.UnregisterVM.side_effect = RuntimeError("locked")
    folder = MagicMock()
    folder.childEntity = [ok, bad]
    with (
        patch.object(vim_vm, "_find_by_type", return_value=folder),
        patch("saltext.vcf.utils.vim.content", return_value=_fake_content()),
    ):
        result = vim_vm.unregister_all(opts, folder="restored")
    assert result["a"]["success"] is True
    assert result["b"]["success"] is False
    assert "locked" in result["b"]["error"]


def test_register_all(tmp_path, opts, monkeypatch):
    files = [
        {"datastore": "ds1", "folder_path": "[ds1] a/", "file_name": "alpha.vmx"},
        {"datastore": "ds1", "folder_path": "[ds1] b/", "file_name": "beta.vmx"},
    ]
    monkeypatch.setattr("saltext.vcf.clients.vim_datastore_file.find_vmx", lambda o, d, **kw: files)
    registered = []

    def _register(opts_, vmx_path, name, folder=None, **kw):
        registered.append((vmx_path, name))

    monkeypatch.setattr(vim_vm, "register", _register)
    result = vim_vm.register_all(opts, "ds1", cluster="cl-1")
    assert registered == [("[ds1] a/alpha.vmx", "alpha"), ("[ds1] b/beta.vmx", "beta")]
    assert all(r["success"] for r in result.values())
