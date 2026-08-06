"""Tests for modules.vcf_vim_vm_devices — USB controller functions (Broadcom KB 316384)."""

import pytest

from saltext.vcf.clients import vim_vm_devices as c
from saltext.vcf.modules import vcf_vim_vm_devices as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_usb_controllers_list_passes_through(monkeypatch):
    monkeypatch.setattr(c, "usb_controllers_list", lambda opts, vm, profile=None: [{"key": 7000}])
    assert mod.usb_controllers_list("vm-100") == [{"key": 7000}]


def test_usb_controllers_remove_passes_through(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "usb_controllers_remove",
        lambda opts, vm, profile=None: calls.append(vm) or [{"key": 7000}],
    )
    result = mod.usb_controllers_remove("vm-100")
    assert result == [{"key": 7000}]
    assert calls == ["vm-100"]


def test_list_vms_with_usb_controllers_passes_through(monkeypatch):
    monkeypatch.setattr(
        c, "list_vms_with_usb_controllers", lambda opts, profile=None: [{"vm": "vm-1"}]
    )
    assert mod.list_vms_with_usb_controllers() == [{"vm": "vm-1"}]
