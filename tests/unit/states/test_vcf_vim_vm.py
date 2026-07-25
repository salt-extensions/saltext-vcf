"""Tests for the ``vcf_vim_vm.resource_pinning_disabled`` state.

Enforces 912 Controls VM-to-CPU / VM-to-Memory pinning prohibitions.
Exercises the drift/no-drift/test-mode paths through mocked exec-module
calls, so the state logic is validated independently of whether the
underlying opts point at vCenter or a standalone ESXi host.
"""

import pytest

from saltext.vcf.states import vcf_vim_vm as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _make_salt(current, calls):
    def _get(_name, profile=None):
        return current

    def _set(_name, **kw):
        calls.append(kw)
        return "task-1"

    return {
        "vcf_vim_vm.get_resource_config": _get,
        "vcf_vim_vm.set_resource_config": _set,
    }


UNPINNED = {
    "cpu_affinity": None,
    "cpu_shares_level": "normal",
    "cpu_shares": 1000,
    "memory_reservation_mb": 0,
    "memory_reservation_locked_to_max": False,
}


def test_resource_pinning_disabled_noop_when_already_cleared(monkeypatch):
    calls = []
    monkeypatch.setattr(st, "__salt__", _make_salt(UNPINNED, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert calls == []
    assert "already" in ret["comment"]


def test_resource_pinning_disabled_clears_cpu_affinity(monkeypatch):
    calls = []
    current = {**UNPINNED, "cpu_affinity": [0, 2]}
    monkeypatch.setattr(st, "__salt__", _make_salt(current, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100")
    assert ret["result"] is True
    assert ret["changes"]["cpu_affinity"] == ([0, 2], [])
    assert len(calls) == 1
    assert calls[0]["cpu_affinity"] == []


def test_resource_pinning_disabled_clears_memory_reservation(monkeypatch):
    calls = []
    current = {
        **UNPINNED,
        "memory_reservation_mb": 4096,
        "memory_reservation_locked_to_max": True,
    }
    monkeypatch.setattr(st, "__salt__", _make_salt(current, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100")
    assert ret["changes"]["memory_reservation_mb"] == (4096, 0)
    assert ret["changes"]["memory_reservation_locked_to_max"] == (True, False)
    assert calls[0]["memory_reservation_mb"] == 0
    assert calls[0]["memory_reservation_locked_to_max"] is False


def test_resource_pinning_disabled_clears_cpu_shares(monkeypatch):
    calls = []
    current = {**UNPINNED, "cpu_shares_level": "high", "cpu_shares": 4000}
    monkeypatch.setattr(st, "__salt__", _make_salt(current, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100")
    assert ret["changes"]["cpu_shares_level"] == ("high", "normal")
    assert ret["changes"]["cpu_shares"] == (4000, 1000)


def test_resource_pinning_disabled_test_mode(monkeypatch, opts):
    opts["test"] = True
    calls = []
    current = {**UNPINNED, "cpu_affinity": [0]}
    monkeypatch.setattr(st, "__salt__", _make_salt(current, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100")
    assert ret["result"] is None
    assert "cpu_affinity" in ret["changes"]
    assert calls == []


def test_resource_pinning_disabled_exception_override(monkeypatch):
    """Callers can pass an explicit non-default affinity for exception cases."""
    calls = []
    current = {**UNPINNED, "cpu_affinity": [0, 1]}
    monkeypatch.setattr(st, "__salt__", _make_salt(current, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100", cpu_affinity=[0, 1])
    # already matches — no change
    assert ret["changes"] == {}
    assert calls == []


def test_resource_pinning_disabled_drift_when_none_current_affinity(monkeypatch):
    """None current + default (cleared) target must be a no-op."""
    calls = []
    current = {**UNPINNED}  # cpu_affinity is None
    monkeypatch.setattr(st, "__salt__", _make_salt(current, calls), raising=False)
    ret = st.resource_pinning_disabled("vm-100")
    assert ret["changes"] == {}
    assert calls == []
