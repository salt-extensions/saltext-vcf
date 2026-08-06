"""Tests for states.vcf_vim_vm_devices.usb_controllers_absent (Broadcom KB 316384).

The tpm/vgpu/serial states in this module have no existing test coverage;
these tests are scoped to only the new fleet-wide USB-controller state.
"""

import pytest

from saltext.vcf.clients import vim_vm_devices as c
from saltext.vcf.states import vcf_vim_vm_devices as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    opts = dict(opts)
    opts["test"] = False
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _found(vm, moid, connected=True, devices=None):
    return {
        "vm": vm,
        "moid": moid,
        "connected": connected,
        "devices": devices if devices is not None else [{"key": 7000, "label": "USB Controller"}],
    }


def test_usb_controllers_absent_noop_when_none_found(monkeypatch):
    monkeypatch.setattr(c, "list_vms_with_usb_controllers", lambda opts, profile=None: [])
    ret = st.usb_controllers_absent("audit")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "no VMs with a USB controller found" in ret["comment"]


def test_usb_controllers_absent_test_mode_reports_without_removing(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c,
        "list_vms_with_usb_controllers",
        lambda opts, profile=None: [_found("vm-1", "moid-1"), _found("vm-2", "moid-2")],
    )
    remove_calls = []
    monkeypatch.setattr(
        c, "usb_controllers_remove", lambda opts, vm, profile=None: remove_calls.append(vm)
    )

    ret = st.usb_controllers_absent("audit")
    assert ret["result"] is None
    assert "vm-1" in ret["comment"] and "vm-2" in ret["comment"]
    assert set(ret["changes"]["would_remove"].keys()) == {"vm-1", "vm-2"}
    assert remove_calls == []


def test_usb_controllers_absent_removes_found_vms(monkeypatch):
    monkeypatch.setattr(
        c,
        "list_vms_with_usb_controllers",
        lambda opts, profile=None: [_found("vm-1", "moid-1")],
    )
    remove_calls = []
    monkeypatch.setattr(
        c,
        "usb_controllers_remove",
        lambda opts, vm, profile=None: remove_calls.append(vm)
        or [{"key": 7000, "label": "USB Controller"}],
    )

    ret = st.usb_controllers_absent("audit")
    assert ret["result"] is True
    assert remove_calls == ["moid-1"]
    assert ret["changes"]["removed"]["vm-1"] == [{"key": 7000, "label": "USB Controller"}]
    assert "removed USB controller(s) from 1 VM(s)" in ret["comment"]


def test_usb_controllers_absent_skips_disconnected_by_default(monkeypatch):
    monkeypatch.setattr(
        c,
        "list_vms_with_usb_controllers",
        lambda opts, profile=None: [
            _found("vm-connected", "moid-1", connected=True),
            _found("vm-disconnected", "moid-2", connected=False),
        ],
    )
    remove_calls = []
    monkeypatch.setattr(
        c,
        "usb_controllers_remove",
        lambda opts, vm, profile=None: remove_calls.append(vm) or [],
    )

    ret = st.usb_controllers_absent("audit")
    assert remove_calls == ["moid-1"]
    assert "vm-disconnected" not in ret["changes"].get("removed", {})


def test_usb_controllers_absent_connected_only_false_includes_disconnected(monkeypatch):
    monkeypatch.setattr(
        c,
        "list_vms_with_usb_controllers",
        lambda opts, profile=None: [_found("vm-disconnected", "moid-2", connected=False)],
    )
    remove_calls = []
    monkeypatch.setattr(
        c,
        "usb_controllers_remove",
        lambda opts, vm, profile=None: remove_calls.append(vm) or [],
    )

    ret = st.usb_controllers_absent("audit", connected_only=False)
    assert remove_calls == ["moid-2"]
    assert ret["result"] is True


def test_usb_controllers_absent_reports_partial_failure(monkeypatch):
    monkeypatch.setattr(
        c,
        "list_vms_with_usb_controllers",
        lambda opts, profile=None: [_found("vm-good", "moid-1"), _found("vm-bad", "moid-2")],
    )

    def fake_remove(opts, vm, profile=None):
        if vm == "moid-2":
            raise RuntimeError("permission denied")
        return [{"key": 7000, "label": "USB Controller"}]

    monkeypatch.setattr(c, "usb_controllers_remove", fake_remove)

    ret = st.usb_controllers_absent("audit")
    assert ret["result"] is False
    assert "vm-good" in ret["changes"]["removed"]
    assert ret["changes"]["errors"]["vm-bad"] == "permission denied"
    assert "failed on 1" in ret["comment"]


def test_usb_controllers_absent_only_disconnected_found_reports_skip_count(monkeypatch):
    monkeypatch.setattr(
        c,
        "list_vms_with_usb_controllers",
        lambda opts, profile=None: [_found("vm-disconnected", "moid-1", connected=False)],
    )
    ret = st.usb_controllers_absent("audit")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "1 disconnected VM(s)" in ret["comment"]
