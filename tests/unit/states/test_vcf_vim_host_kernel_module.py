"""Tests for the vim_host_kernel_module state module."""

import pytest

from saltext.vcf.clients import vim_host_kernel_module as c
from saltext.vcf.states import vcf_vim_host_kernel_module as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_options_already_match(monkeypatch):
    monkeypatch.setattr(c, "get_options", lambda o, h, m, profile=None: "max_vfs=8")
    ret = st.options_set("ixgbe", host="esx-1", options="max_vfs=8")
    assert ret["changes"] == {}
    assert ret["result"] is True


def test_options_drift_applied(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_options", lambda o, h, m, profile=None: "max_vfs=4")
    monkeypatch.setattr(c, "set_options", lambda o, h, m, v, profile=None: calls.append((m, v)))
    ret = st.options_set("ixgbe", host="esx-1", options="max_vfs=8")
    assert ret["changes"]["options"] == ("max_vfs=4", "max_vfs=8")
    assert calls == [("ixgbe", "max_vfs=8")]


def test_test_mode_dry_run(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get_options", lambda o, h, m, profile=None: "max_vfs=4")
    monkeypatch.setattr(
        c, "set_options", lambda *a, **kw: pytest.fail("should not write in test mode")
    )
    ret = st.options_set("ixgbe", host="esx-1", options="max_vfs=8")
    assert ret["result"] is None
    assert ret["changes"] == {}


def test_missing_options_fails():
    ret = st.options_set("ixgbe", host="esx-1")
    assert ret["result"] is False
