"""Tests for the vcf_vsan_disk state module (host-level vSAN config)."""

import pytest

from saltext.vcf.clients import vsan_disk as c
from saltext.vcf.states import vcf_vsan_disk as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_already_enabled(monkeypatch):
    monkeypatch.setattr(c, "host_config", lambda o, h, profile=None: {"enabled": True})
    ret = st.host_configured("vsan", "esxi-01", True)
    assert ret["changes"] == {}


def test_enables(monkeypatch):
    monkeypatch.setattr(c, "host_config", lambda o, h, profile=None: {"enabled": False})
    called = []
    monkeypatch.setattr(c, "host_enable", lambda o, h, e, profile=None: called.append(e))
    ret = st.host_configured("vsan", "esxi-01", True)
    assert ret["changes"] == {"enabled": (False, True)}
    assert called == [True]


def test_test_mode(monkeypatch):
    monkeypatch.setattr(c, "host_config", lambda o, h, profile=None: {"enabled": False})
    monkeypatch.setattr(c, "host_enable", lambda *a, **kw: pytest.fail("must not enable"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.host_configured("vsan", "esxi-01", True)
    assert ret["result"] is None
