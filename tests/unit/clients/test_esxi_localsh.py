"""Tests for clients.esxi_localsh (SSH-managed local.sh)."""

from unittest.mock import patch

import pytest

from saltext.vcf.clients import esxi_localsh as c


def test_render_includes_all_features():
    content = c.render({"a": "echo one", "b": "echo two"})
    assert "echo one" in content
    assert "echo two" in content
    assert content.startswith("#!/bin/sh")
    assert content.rstrip().endswith("exit 0")


def test_get_returns_none_when_absent(opts):
    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", return_value=(1, "", "no file")):
        assert c.get(opts) is None


def test_get_returns_content(opts):
    with patch(
        "saltext.vcf.clients.esxi_localsh.ssh_util.run", return_value=(0, "#!/bin/sh\nexit 0\n", "")
    ):
        assert c.get(opts) == "#!/bin/sh\nexit 0\n"


def test_apply_writes_both_paths_and_executes(opts):
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        return 0, "", ""

    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", side_effect=fake_run):
        c.apply(opts, "#!/bin/sh\nexit 0\n", execute=True)
    assert len(calls) == 3
    assert c.REMOTE_PATH in calls[0]
    assert c.EXEC_PATH in calls[1]
    assert calls[2] == c.EXEC_PATH


def test_apply_skips_execution_when_execute_false(opts):
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        return 0, "", ""

    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", side_effect=fake_run):
        c.apply(opts, "#!/bin/sh\nexit 0\n", execute=False)
    assert len(calls) == 1
    assert c.REMOTE_PATH in calls[0]


def test_apply_raises_on_write_failure(opts):
    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", return_value=(1, "", "denied")):
        with pytest.raises(RuntimeError, match="denied"):
            c.apply(opts, "#!/bin/sh\nexit 0\n")


def test_apply_raises_on_exec_failure(opts):
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        if cmd == c.EXEC_PATH:
            return 1, "", "boom"
        return 0, "", ""

    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", side_effect=fake_run):
        with pytest.raises(RuntimeError, match="boom"):
            c.apply(opts, "#!/bin/sh\nexit 0\n")
