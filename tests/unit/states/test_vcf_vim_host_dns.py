"""Tests for the vim_host_dns state module."""

import pytest

from saltext.vcf.clients import vim_host_dns as c
from saltext.vcf.states import vcf_vim_host_dns as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _cur(**overrides):
    base = {
        "dhcp": False,
        "hostname": "esx-1",
        "domain_name": "example.com",
        "servers": ["10.0.0.1"],
        "search_domains": ["example.com"],
        "virtual_nic": None,
    }
    base.update(overrides)
    return base


def test_already_matches(monkeypatch):
    monkeypatch.setattr(c, "get", lambda o, h, profile=None: _cur())
    ret = st.config("esx-1", servers=["10.0.0.1"], search_domains=["example.com"])
    assert ret["changes"] == {}


def test_drift_servers(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get", lambda o, h, profile=None: _cur())
    monkeypatch.setattr(c, "set_", lambda *a, **kw: calls.append(kw) or None)
    ret = st.config("esx-1", servers=["10.0.0.2"])
    assert ret["changes"]["servers"] == (["10.0.0.1"], ["10.0.0.2"])
    assert calls[0]["servers"] == ["10.0.0.2"]


def test_drift_multiple(monkeypatch):
    monkeypatch.setattr(c, "get", lambda o, h, profile=None: _cur())
    monkeypatch.setattr(c, "set_", lambda *a, **kw: None)
    ret = st.config("esx-1", hostname="esx-renamed", search_domains=["foo.example.com"])
    assert "hostname" in ret["changes"]
    assert "search_domains" in ret["changes"]


def test_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get", lambda o, h, profile=None: _cur())
    monkeypatch.setattr(c, "set_", lambda *a, **kw: pytest.fail("should not write"))
    ret = st.config("esx-1", servers=["10.0.0.2"])
    assert ret["result"] is None
    assert ret["changes"] == {}
