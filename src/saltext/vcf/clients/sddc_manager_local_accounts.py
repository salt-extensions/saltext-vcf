"""Local OS users client for SDDC Manager (``/etc/passwd`` over SSH).

Remote equivalent of the ``mops`` config-modules ``local_os_users`` control
(configuration id 1617): it reads ``/etc/passwd`` on the SDDC Manager appliance
and returns the OS user inventory. ``/etc/passwd`` is world-readable, so no
privilege escalation is required (matching the "zero sudo" design of the
on-appliance control).

There is **no remote SDDC Manager REST API** that exposes the OS user list
(the ``/v1/users/local-accounts`` endpoint returns application/SSO accounts,
a different dataset, and is not present on all builds), so this client connects
over SSH and reads the file directly. SSH config is read from
``saltext.vcf.sddc_manager.ssh``:

.. code-block:: yaml

    saltext.vcf:
      sddc_manager:
        host: sddc-manager.example.test
        ssh:
          host: sddc-manager.example.test   # optional; defaults to host
          username: root
          password: secret
"""

import logging

from saltext.vcf.utils import sddc
from saltext.vcf.utils import ssh as ssh_util

log = logging.getLogger(__name__)

PASSWD_FILE = "/etc/passwd"


def _parse_passwd(content):
    """Parse ``/etc/passwd`` text into a list of user dicts.

    Each line has 7 colon-separated fields
    (``username:password:uid:gid:gecos:home:shell``); the password field
    (always ``x``) is discarded. Blank lines, comments and malformed lines
    are skipped.

    :param content: Raw ``/etc/passwd`` contents.
    :return: List of dicts with keys ``username``, ``uid``, ``gid``,
        ``gecos``, ``home``, ``shell``.
    """
    users = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 6)
        if len(parts) != 7:
            continue
        username, _password, uid_str, gid_str, gecos, home, shell = parts
        try:
            users.append(
                {
                    "username": username,
                    "uid": int(uid_str),
                    "gid": int(gid_str),
                    "gecos": gecos,
                    "home": home,
                    "shell": shell,
                }
            )
        except ValueError:
            log.warning("Skipping malformed passwd line for user %r", username)
    return users


def list_(opts, profile=None):
    """Return the OS user inventory from ``/etc/passwd`` on SDDC Manager.

    :param opts: Salt opts / pillar dict.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.
    :return: List of user dicts (see :func:`_parse_passwd`).
    :raises RuntimeError: if the file cannot be read over SSH.
    """
    ssh_cfg = sddc.get_ssh_config(opts, profile=profile)
    rc, out, err = ssh_util.run(ssh_cfg, f"cat {PASSWD_FILE}")
    if rc != 0:
        raise RuntimeError(
            f"Failed to read {PASSWD_FILE} on {ssh_cfg.get('host')}: rc={rc} {err.strip()}"
        )
    return _parse_passwd(out)


def list_or_none(opts, profile=None):
    """Return the OS user list, or ``None`` if it cannot be retrieved."""
    try:
        return list_(opts, profile=profile)
    except Exception as exc:  # noqa: BLE001 - audit control degrades to "unknown"
        log.warning("Could not read local OS users from SDDC Manager: %s", exc)
        return None
