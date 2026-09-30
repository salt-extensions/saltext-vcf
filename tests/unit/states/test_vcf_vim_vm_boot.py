"""Tests for the vcf_vim_vm_boot state module."""

import pytest

from saltext.vcf.clients import vim_vm_boot as c
from saltext.vcf.states import vcf_vim_vm_boot as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


_CURRENT = {
    "order": ["cdrom", "disk"],
    "delay": 0,
    "enter_bios_setup": False,
    "retry_enabled": False,
    "retry_delay": 10000,
    "efi_secure_boot_enabled": False,
}


def test_already_configured(monkeypatch):
    monkeypatch.setattr(c, "get", lambda o, v, profile=None: dict(_CURRENT))
    ret = st.boot_manager(
        "vm-100",
        boot_order=["cdrom", "disk"],
        delay=0,
        enter_bios_setup=False,
        retry_enabled=False,
        retry_delay=10000,
        efi_secure_boot=False,
    )
    assert ret["changes"] == {}
    assert ret["result"] is True


def test_drift_reported_and_applied(monkeypatch):
    monkeypatch.setattr(c, "get", lambda o, v, profile=None: dict(_CURRENT))
    calls = {}
    monkeypatch.setattr(
        c,
        "set",
        lambda o, v, **kw: calls.update(kw) or "task-1",
    )
    ret = st.boot_manager("vm-100", delay=5000, retry_enabled=True)
    assert ret["result"] is True
    assert ret["changes"] == {
        "delay": (0, 5000),
        "retry_enabled": (False, True),
    }
    assert calls["delay"] == 5000
    assert calls["retry_enabled"] is True


def test_test_mode_reports_without_calling_set(monkeypatch):
    monkeypatch.setattr(c, "get", lambda o, v, profile=None: dict(_CURRENT))
    called = []
    monkeypatch.setattr(c, "set", lambda o, v, **kw: called.append(kw))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.boot_manager("vm-100", delay=5000)
    assert ret["result"] is None
    assert ret["changes"] == {"delay": (0, 5000)}
    assert called == []
