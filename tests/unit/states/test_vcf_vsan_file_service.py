"""Tests for states.vcf_vsan_file_service."""

import pytest

from saltext.vcf.clients import vsan_file_service as c
from saltext.vcf.states import vcf_vsan_file_service as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


ARGS = {
    "cluster": "SDDC-Cluster1",
    "network_name": "VM-Mgmt",
    "domain_name": "fileshare",
    "ip_to_fqdn": {"10.0.0.1": "f0.test"},
    "subnet_mask": "255.255.255.0",
    "gateway_address": "10.0.0.250",
    "dns_suffixes": ["test"],
    "dns_address": ["10.0.0.250"],
}


def test_configured_already_done(monkeypatch):
    monkeypatch.setattr(c, "enabled", lambda opts, cluster, profile=None: True)
    monkeypatch.setattr(c, "domain_exists", lambda opts, cluster, domain_name, profile=None: True)
    ret = st.configured("vsan-fs", **ARGS)
    assert ret["changes"] == {}


def test_configured_enables_and_creates_domain(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "enabled", lambda opts, cluster, profile=None: False)
    monkeypatch.setattr(c, "domain_exists", lambda opts, cluster, domain_name, profile=None: False)
    monkeypatch.setattr(
        c, "download_ovf", lambda opts, cluster, ovf_url=None, profile=None: calls.append("ovf")
    )
    monkeypatch.setattr(
        c,
        "set_enabled",
        lambda opts, cluster, enabled_, network_name=None, profile=None: calls.append("enable")
        or "task-1",
    )
    monkeypatch.setattr(
        c,
        "create_domain",
        lambda opts, cluster, domain_name, ip_to_fqdn, subnet_mask, gateway_address, dns_suffixes, dns_address, profile=None: calls.append(
            "domain"
        )
        or "task-2",
    )
    ret = st.configured("vsan-fs", **ARGS)
    assert calls == ["ovf", "enable", "domain"]
    assert ret["changes"]["enabled"]["task_id"] == "task-1"
    assert ret["changes"]["domain"]["task_id"] == "task-2"


def test_configured_test_mode(monkeypatch):
    monkeypatch.setattr(c, "enabled", lambda opts, cluster, profile=None: False)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.configured("vsan-fs", **ARGS)
    assert ret["result"] is None


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "domain_exists", lambda opts, cluster, domain_name, profile=None: False)
    monkeypatch.setattr(c, "enabled", lambda opts, cluster, profile=None: False)
    ret = st.absent("vsan-fs", "SDDC-Cluster1", domain_name="fileshare")
    assert ret["changes"] == {}


def test_absent_removes_domain_and_disables(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "domain_exists", lambda opts, cluster, domain_name, profile=None: True)
    monkeypatch.setattr(c, "enabled", lambda opts, cluster, profile=None: True)
    monkeypatch.setattr(
        c,
        "remove_domain",
        lambda opts, cluster, domain_name, profile=None: calls.append("remove") or "task-3",
    )
    monkeypatch.setattr(
        c,
        "set_enabled",
        lambda opts, cluster, enabled_, network_name=None, profile=None: calls.append("disable")
        or "task-4",
    )
    ret = st.absent("vsan-fs", "SDDC-Cluster1", domain_name="fileshare")
    assert calls == ["remove", "disable"]
    assert ret["changes"]["domain"]["task_id"] == "task-3"
    assert ret["changes"]["enabled"]["task_id"] == "task-4"
