"""ESXi ``/etc/rc.local.d/local.sh`` (custom boot-time commands) over SSH.

Like netdump, this is genuinely filesystem-level ESXi host config with no
vim25 or vAPI equivalent — the Ansible role it ports (``esxi_localsh``)
reaches it the same way, over SSH via ``ansible.builtin.template``. Files
are written with a base64 pipe rather than a heredoc to avoid quoting
issues in ESXi's busybox ``sh``.

The unusual file modes below (``other`` getting write+execute while
``owner`` only gets read/read+execute) are copied verbatim from the
Ansible role's ``local.sh``/``local_exec.sh`` tasks — surprising, but not
this port's call to "fix".
"""

import base64

from saltext.vcf.utils import esxi
from saltext.vcf.utils import ssh as ssh_util

REMOTE_PATH = "/etc/rc.local.d/local.sh"
EXEC_PATH = "/etc/rc.local.d/local_exec.sh"
_PERSISTED_MODE = "0457"  # u=r,g=rx,o=rwx, matching the Ansible role verbatim
_EXEC_MODE = "0557"  # u=rx,g=rx,o=rwx


def render(features):
    """Render ``local.sh`` content from a ``{label: shell_command}`` dict."""
    lines = [
        "#!/bin/sh ++group=host/vim/vmvisor/boot",
        "",
        "# local configuration options",
        "",
    ]
    lines.extend(str(command) for command in features.values())
    lines.append("")
    lines.append("exit 0")
    lines.append("")
    return "\n".join(lines)


def get(opts, profile=None):
    """Return the current contents of ``local.sh``, or ``None`` if absent."""
    ssh_cfg = esxi.get_ssh_config(opts, profile=profile)
    rc, out, _err = ssh_util.run(ssh_cfg, f"cat {REMOTE_PATH} 2>/dev/null")
    return out if rc == 0 and out else None


def apply(opts, content, execute=True, profile=None):
    """Write *content* to the persisted ``local.sh`` and, unless *execute* is
    ``False``, also write it to the exec path and run it immediately —
    mirroring the Ansible role's "generate, then apply now" behavior rather
    than waiting for the next reboot.
    """
    ssh_cfg = esxi.get_ssh_config(opts, profile=profile)
    _write_file(ssh_cfg, REMOTE_PATH, content, _PERSISTED_MODE)
    if not execute:
        return None
    _write_file(ssh_cfg, EXEC_PATH, content, _EXEC_MODE)
    rc, out, err = ssh_util.run(ssh_cfg, EXEC_PATH)
    if rc != 0:
        raise RuntimeError(f"{EXEC_PATH} failed on {ssh_cfg.get('host')}: {err.strip()}")
    return out


def _write_file(ssh_cfg, path, content, mode):
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    cmd = f"echo {encoded} | base64 -d > {path} && chmod {mode} {path} && chown root:root {path}"
    rc, _out, err = ssh_util.run(ssh_cfg, cmd)
    if rc != 0:
        raise RuntimeError(f"failed writing {path} on {ssh_cfg.get('host')}: {err.strip()}")
