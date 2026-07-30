"""Tests for clients.vrli_settings (REST reads + SSH-mocked writes)."""

from unittest import mock

import pytest
import responses

from saltext.vcf.clients import vrli_settings

_NODES_URL = "https://vrli.test:9543/api/v2/cluster/nodes"


def _node(ip="25.0.3.124", dns="25.0.0.1 25.0.0.2 2001:db8::1", primary=True):
    return {
        "id": "n1",
        "ip": ip,
        "isPrimary": primary,
        "dnsServers": dns,
        "gateway": "25.0.0.1",
        "netmask": "255.255.252.0",
    }


def test_get_cluster_nodes_returns_nodes_array(opts, vrli_authed):
    vrli_authed.add(responses.GET, _NODES_URL, json={"nodes": [_node()]}, status=200)
    out = vrli_settings.get_cluster_nodes(opts)
    assert out[0]["ip"] == "25.0.3.124"


def test_get_dns_servers_filters_ipv4_from_primary(opts, vrli_authed):
    vrli_authed.add(
        responses.GET,
        _NODES_URL,
        json={"nodes": [_node(dns="10.0.0.53 10.0.0.54 fe80::1"), _node(primary=False)]},
        status=200,
    )
    assert vrli_settings.get_dns_servers(opts) == ["10.0.0.53", "10.0.0.54"]


def test_get_dns_servers_falls_back_to_first_node(opts, vrli_authed):
    """No node has isPrimary=true — take the first."""
    vrli_authed.add(
        responses.GET,
        _NODES_URL,
        json={"nodes": [_node(primary=False, dns="8.8.8.8")]},
        status=200,
    )
    assert vrli_settings.get_dns_servers(opts) == ["8.8.8.8"]


def test_get_dns_servers_empty_when_no_nodes(opts, vrli_authed):
    vrli_authed.add(responses.GET, _NODES_URL, json={"nodes": []}, status=200)
    assert vrli_settings.get_dns_servers(opts) == []


def test_get_session_timeout_reads_web_xml_over_ssh(opts):
    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run") as run:
        run.return_value = (0, "30\n", "")
        assert vrli_settings.get_session_timeout(opts) == 1800
    assert "web.xml" in run.call_args[0][1]


def test_get_session_timeout_raises_on_ssh_failure(opts):
    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run") as run:
        run.return_value = (1, "", "permission denied")
        with pytest.raises(RuntimeError):
            vrli_settings.get_session_timeout(opts)


def test_set_session_timeout_writes_minutes_and_restarts(opts):
    calls = []

    def _fake_run(_cfg, cmd, **_kw):
        calls.append(cmd)
        if cmd.startswith("sed "):
            return (0, "", "")
        if cmd.startswith("grep "):
            return (0, "30\n", "")
        if cmd.startswith("systemctl "):
            return (0, "", "")
        return (0, "", "")

    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run", side_effect=_fake_run):
        out = vrli_settings.set_session_timeout(opts, 1800)
    assert out == {"session_timeout_seconds": 1800, "restart_requested": True}
    assert any("session-timeout>30" in c for c in calls)
    assert any(c.startswith("systemctl restart loginsight") for c in calls)


def test_set_session_timeout_verify_mismatch_raises(opts):
    def _fake_run(_cfg, cmd, **_kw):
        if cmd.startswith("sed "):
            return (0, "", "")
        if cmd.startswith("grep "):
            return (0, "45\n", "")  # not what we asked for
        return (0, "", "")

    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run", side_effect=_fake_run):
        with pytest.raises(RuntimeError):
            vrli_settings.set_session_timeout(opts, 1800)


def test_get_dns_servers_from_appliance_parses_networkd(opts):
    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run") as run:
        run.return_value = (0, "DNS=10.0.0.53\nDNS=10.0.0.54\n", "")
        assert vrli_settings.get_dns_servers_from_appliance(opts) == [
            "10.0.0.53",
            "10.0.0.54",
        ]


def test_set_dns_servers_rewrites_and_applies(opts):
    calls = []

    def _fake_run(_cfg, cmd, **_kw):
        calls.append(cmd)
        return (0, "", "")

    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run", side_effect=_fake_run):
        out = vrli_settings.set_dns_servers(opts, ["10.0.0.53", "10.0.0.54"])
    assert out == {"dns_servers": ["10.0.0.53", "10.0.0.54"], "applied": True}
    cmd = calls[-1]
    assert "10.0.0.53" in cmd and "10.0.0.54" in cmd
    assert "networkctl reload" in cmd
    assert "systemctl restart systemd-resolved" in cmd


def test_set_dns_servers_rejects_non_ipv4(opts):
    with pytest.raises(ValueError):
        vrli_settings.set_dns_servers(opts, ["not.an.address"])


def test_set_dns_servers_raises_on_ssh_failure(opts):
    with mock.patch("saltext.vcf.clients.vrli_settings.ssh_util.run") as run:
        run.return_value = (1, "", "denied")
        with pytest.raises(RuntimeError):
            vrli_settings.set_dns_servers(opts, ["10.0.0.53"])
