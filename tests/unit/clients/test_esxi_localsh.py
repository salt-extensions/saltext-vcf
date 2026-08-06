"""Tests for clients.esxi_localsh (SSH-managed local.sh)."""

import base64
from unittest.mock import patch

import pytest

from saltext.vcf.clients import esxi_localsh as c

FEATURES = {"a": "echo one", "b": "echo two"}


def _decoded_payload(cmd):
    """Extract and decode the base64 blob from a ``_write_file`` command string."""
    encoded = cmd.split("echo ", 1)[1].split(" | base64 -d", 1)[0]
    return base64.b64decode(encoded).decode("utf-8")


def test_render_includes_all_features_and_exit_stub_by_default():
    content = c.render(FEATURES)
    assert "echo one" in content
    assert "echo two" in content
    assert content.startswith("#!/bin/sh")
    assert content.rstrip().endswith("exit 0")


def test_render_omits_exit_stub_when_requested():
    """The exec variant must NOT end with exit 0 -- matching the Ansible
    template's ``{% if not esxi_localsh_localsh_exec %}exit 0{% endif %}``
    -- otherwise the script's real exit status (the last embedded
    command's) never propagates and failures go undetected.
    """
    content = c.render(FEATURES, include_exit_stub=False)
    assert "echo two" in content
    assert "exit 0" not in content


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
        c.apply(opts, FEATURES, execute=True)
    assert len(calls) == 3
    assert c.REMOTE_PATH in calls[0]
    assert c.EXEC_PATH in calls[1]
    assert calls[2] == c.EXEC_PATH


def test_apply_writes_exit_stub_only_on_persisted_path(opts):
    """The persisted local.sh must keep its exit 0 safety stub; the exec
    variant written to EXEC_PATH must not, so its real exit status is what
    gets checked.
    """
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        return 0, "", ""

    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", side_effect=fake_run):
        c.apply(opts, FEATURES, execute=True)

    persisted_payload = _decoded_payload(calls[0])
    exec_payload = _decoded_payload(calls[1])
    assert persisted_payload.rstrip().endswith("exit 0")
    assert "exit 0" not in exec_payload


def test_apply_skips_execution_when_execute_false(opts):
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        return 0, "", ""

    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", side_effect=fake_run):
        c.apply(opts, FEATURES, execute=False)
    assert len(calls) == 1
    assert c.REMOTE_PATH in calls[0]


def test_apply_raises_on_write_failure(opts):
    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", return_value=(1, "", "denied")):
        with pytest.raises(RuntimeError, match="denied"):
            c.apply(opts, FEATURES)


def test_apply_raises_on_exec_failure(opts):
    """A real command failure inside the exec script (no more masked by a
    hardcoded trailing exit 0) must surface as a RuntimeError.
    """
    calls = []

    def fake_run(ssh_cfg, cmd):
        calls.append(cmd)
        if cmd == c.EXEC_PATH:
            return 1, "", "boom"
        return 0, "", ""

    with patch("saltext.vcf.clients.esxi_localsh.ssh_util.run", side_effect=fake_run):
        with pytest.raises(RuntimeError, match="boom"):
            c.apply(opts, FEATURES)
