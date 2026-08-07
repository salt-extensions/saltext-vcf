"""Tests for clients.esxi_netdump (esxcli over SSH)."""

from unittest.mock import patch

import pytest

from saltext.vcf.clients import esxi_netdump as c

GET_OUTPUT = """
   Enabled: true
   Host VNic: vmk0
   Network Server IP: 10.0.0.5
   Network Server Port: 6500
"""


def test_get_parses_output(opts):
    with patch("saltext.vcf.clients.esxi_netdump.ssh_util.run", return_value=(0, GET_OUTPUT, "")):
        result = c.get(opts)
    assert result == {
        "enabled": True,
        "interface_name": "vmk0",
        "server_ip": "10.0.0.5",
        "server_port": 6500,
    }


def test_get_raises_on_nonzero_rc(opts):
    with patch("saltext.vcf.clients.esxi_netdump.ssh_util.run", return_value=(1, "", "boom")):
        with pytest.raises(RuntimeError, match="boom"):
            c.get(opts)


def test_set_network_calls_esxcli_with_expected_args(opts):
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        return 0, GET_OUTPUT, ""

    with patch("saltext.vcf.clients.esxi_netdump.ssh_util.run", side_effect=fake_run):
        c.set_network(opts, "vmk0", "10.0.0.5", 6500)
    assert calls == [
        "esxcli system coredump network set "
        "--interface-name=vmk0 --server-ip=10.0.0.5 --server-port=6500"
    ]


def test_set_enabled_true(opts):
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        return 0, GET_OUTPUT, ""

    with patch("saltext.vcf.clients.esxi_netdump.ssh_util.run", side_effect=fake_run):
        c.set_enabled(opts, True)
    assert calls == ["esxcli system coredump network set --enable=true"]


def test_set_enabled_raises_on_failure(opts):
    with patch("saltext.vcf.clients.esxi_netdump.ssh_util.run", return_value=(1, "", "denied")):
        with pytest.raises(RuntimeError, match="denied"):
            c.set_enabled(opts, False)
