"""Tests for states.vcf_esxi_netdump."""

import pytest

from saltext.vcf.clients import esxi_netdump as c
from saltext.vcf.states import vcf_esxi_netdump as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


CURRENT = {"interface_name": "vmk0", "server_ip": "10.0.0.5", "server_port": 6500, "enabled": True}


def test_already_configured(monkeypatch):
    monkeypatch.setattr(c, "get", lambda opts, profile=None: dict(CURRENT))
    ret = st.configured("netdump", "vmk0", "10.0.0.5", 6500, enabled=True)
    assert ret["changes"] == {}


def test_changes_network_and_enabled(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get", lambda opts, profile=None: dict(CURRENT))
    monkeypatch.setattr(
        c,
        "set_network",
        lambda opts, interface_name, server_ip, server_port, profile=None: calls.append(
            ("net", interface_name, server_ip, server_port)
        ),
    )
    monkeypatch.setattr(
        c, "set_enabled", lambda opts, enabled, profile=None: calls.append(("enabled", enabled))
    )
    ret = st.configured("netdump", "vmk1", "10.0.0.9", 6501, enabled=False)
    assert calls == [("net", "vmk1", "10.0.0.9", 6501), ("enabled", False)]
    assert set(ret["changes"]) == {"interface_name", "server_ip", "server_port", "enabled"}


def test_test_mode(monkeypatch):
    monkeypatch.setattr(c, "get", lambda opts, profile=None: dict(CURRENT))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.configured("netdump", "vmk1", "10.0.0.9", 6501, enabled=False)
    assert ret["result"] is None
