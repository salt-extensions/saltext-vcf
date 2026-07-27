"""Tests for modules.vcf_sddc_ceip."""

import pytest

from saltext.vcf.clients import sddc_ceip as c
from saltext.vcf.clients import sddc_tasks
from saltext.vcf.modules import vcf_sddc_ceip as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_get_delegates(monkeypatch):
    monkeypatch.setattr(
        c, "get", lambda _opts, profile=None: {"status": "ENABLED", "instanceId": "abc"}
    )
    assert mod.get() == {"status": "ENABLED", "instanceId": "abc"}


def test_status_delegates(monkeypatch):
    monkeypatch.setattr(c, "status", lambda _opts, profile=None: "DISABLED")
    assert mod.status() == "DISABLED"


def test_is_enabled_delegates(monkeypatch):
    monkeypatch.setattr(c, "is_enabled", lambda _opts, profile=None: True)
    assert mod.is_enabled() is True


def test_set_delegates(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "set_",
        lambda _opts, enabled, profile=None: calls.append(bool(enabled)) or {"id": "t"},
    )
    assert mod.set_(False) == {"id": "t"}
    assert calls == [False]


def test_enable_delegates(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "enable",
        lambda _opts, profile=None: calls.append("enable") or {"id": "t"},
    )
    mod.enable()
    assert calls == ["enable"]


def test_disable_delegates(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "disable",
        lambda _opts, profile=None: calls.append("disable") or {"id": "t"},
    )
    mod.disable()
    assert calls == ["disable"]


def test_wait_delegates(monkeypatch):
    calls = []

    def _wait(_opts, task_id, timeout=3600, poll_interval=10, profile=None):
        calls.append((task_id, timeout, poll_interval))
        return {"id": task_id, "status": "Successful"}

    monkeypatch.setattr(sddc_tasks, "wait", _wait)
    assert mod.wait("t-1", timeout=60, poll_interval=2)["status"] == "Successful"
    assert calls == [("t-1", 60, 2)]
