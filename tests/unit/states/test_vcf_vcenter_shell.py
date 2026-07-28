"""Tests for states.vcf_vcenter_shell."""

import pytest

from saltext.vcf.clients import vcenter_shell as c
from saltext.vcf.states import vcf_vcenter_shell as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "shell": {"enabled": True, "timeout": 0},
        "shell_set_calls": [],
    }

    monkeypatch.setattr(c, "shell_get", lambda opts, profile=None: state["shell"])
    monkeypatch.setattr(
        c,
        "shell_set",
        lambda opts, enabled, timeout=None, profile=None: state["shell_set_calls"].append(
            (enabled, timeout)
        ),
    )
    return state


def test_shell_no_change(stub):
    stub["shell"] = {"enabled": False, "timeout": 0}
    ret = st.shell_access("name", False)
    assert ret["changes"] == {}
    assert stub["shell_set_calls"] == []


def test_shell_changes_enabled(stub):
    stub["shell"] = {"enabled": True, "timeout": 0}
    ret = st.shell_access("name", False)
    assert ret["changes"]["enabled"] == {"old": True, "new": False}
    assert stub["shell_set_calls"] == [(False, None)]


def test_shell_changes_timeout(stub):
    stub["shell"] = {"enabled": True, "timeout": 0}
    ret = st.shell_access("name", True, timeout=30)
    assert ret["changes"]["timeout"] == {"old": 0, "new": 30}
    assert stub["shell_set_calls"] == [(True, 30)]


def test_shell_test_mode(monkeypatch, stub):
    stub["shell"] = {"enabled": True, "timeout": 0}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.shell_access("name", False)
    assert ret["result"] is None
    assert stub["shell_set_calls"] == []
