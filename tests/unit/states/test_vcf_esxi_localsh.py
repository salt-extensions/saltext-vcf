"""Tests for states.vcf_esxi_localsh."""

import pytest

from saltext.vcf.clients import esxi_localsh as c
from saltext.vcf.states import vcf_esxi_localsh as st

FEATURES = {"disable_usb": "/etc/init.d/usbarbitrator stop"}


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_already_matches(monkeypatch):
    rendered = c.render(FEATURES)
    monkeypatch.setattr(c, "get", lambda opts, profile=None: rendered)
    ret = st.managed("local.sh", FEATURES)
    assert ret["changes"] == {}


def test_updates_when_different(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get", lambda opts, profile=None: "#!/bin/sh\nexit 0\n")
    monkeypatch.setattr(
        c,
        "apply",
        lambda opts, content, execute=True, profile=None: calls.append((content, execute)),
    )
    ret = st.managed("local.sh", FEATURES)
    assert ret["changes"]["new"] == c.render(FEATURES)
    assert calls == [(c.render(FEATURES), True)]


def test_test_mode(monkeypatch):
    monkeypatch.setattr(c, "get", lambda opts, profile=None: "#!/bin/sh\nexit 0\n")
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.managed("local.sh", FEATURES)
    assert ret["result"] is None
