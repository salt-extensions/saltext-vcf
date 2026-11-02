"""Local SSO group presence via the appliance's dir-cli, not identity REST.

Requires vCenter Bash/SSH and ``saltext.vcf.vcenter.ssh`` credentials.
SSO authentication uses the existing vCenter username/password. Only local
SSO groups are supported; descriptions are set at creation, not reconciled.
"""

import re
import shlex

from saltext.vcf.utils import ssh

_DIR = "/usr/lib/vmware-vmafd/bin/dir-cli"
_DOMAIN = "/usr/lib/vmware-vmafd/bin/vmafd-cli get-domain-name --server-name localhost"


def _config(opts, profile):
    root = opts.get("pillar", {}).get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("vcenter", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vcenter", cfg)
    connection = dict(cfg.get("ssh") or {})
    connection.setdefault("host", cfg.get("host") or cfg.get("hostname"))
    # Unlike older appliance controls, this authentication control requires
    # a trusted host key. known_hosts is a path on the minion container.
    connection["verify_host_key"] = True
    if not all(connection.get(k) for k in ("host", "username", "password")):
        raise ValueError(
            "Configure saltext.vcf.vcenter.ssh host/username/password for local SSO groups"
        )
    login = cfg.get("username") or cfg.get("user")
    password = cfg.get("password")
    if not login or not isinstance(password, str) or not password:
        raise ValueError("Configure vCenter SSO username/password for dir-cli")
    if any(c in password for c in ("\n", "\r", "\0", "\b")):
        raise ValueError("SSO password contains characters unsupported by the dir-cli stdin prompt")
    return connection, login, password


def _validate_text(value, label):
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(c in value for c in "\r\n\0")
    ):
        raise ValueError(f"{label} must be a nonempty single-line string")


def _context(opts, name, domain, profile):
    _validate_text(name, "Group name")
    _validate_text(domain, "SSO domain")
    connection, login, password = _config(opts, profile)
    rc, out, _ = ssh.run(connection, _DOMAIN)
    if rc or not out.strip():
        raise RuntimeError("Cannot read the appliance SSO domain; verify SSH access and Bash shell")
    if out.strip().casefold() != domain.casefold():
        raise ValueError(f"Requested domain {domain!r} is not the appliance's local SSO domain")
    return connection, login, password


def _run(context, arguments):
    connection, login, password = context
    command = shlex.join([_DIR, *arguments, "--login", login])
    rc, out, err = ssh.run(connection, command, input_data=password + "\n")
    # Never include arbitrary CLI output (which may contain credentials) in
    # Salt returns. Preserve the numeric dir-cli diagnostic for troubleshooting.
    diagnostic = re.search(r"dir-cli failed\. Error (\d+):", out + "\n" + err)
    return rc, int(diagnostic.group(1)) if diagnostic else None


def _exists(context, name):
    rc, error = _run(context, ["group", "list", "--name", name])
    if rc == 0 and error is None:
        return True  # An empty group's member listing is also success.
    if rc != 0 and error == 1319:  # ERROR_NO_SUCH_GROUP, not any generic failure
        return False
    raise RuntimeError(f"SSO group lookup failed (exit {rc}, dir-cli error {error})")


def get_or_none(opts, name, domain, profile=None):
    """Return a presence record; authentication/transport failures propagate."""
    context = _context(opts, name, domain, profile)
    return {"name": name, "domain": domain} if _exists(context, name) else None


def create(opts, name, domain, description="", profile=None):
    """Create a local SSO group and verify its presence before reporting success."""
    context = _context(opts, name, domain, profile)
    if not isinstance(description, str) or any(c in description for c in "\r\n\0"):
        raise ValueError("Group description must be a single-line string")
    rc, error = _run(
        context, ["ssogroup", "create", "--name", name, "--description", description]
    )
    if rc or error is not None:
        raise RuntimeError(f"SSO group creation failed (exit {rc}, dir-cli error {error})")
    if not _exists(context, name):
        raise RuntimeError("dir-cli returned success but the SSO group was not found on verification")
    return {"name": name, "domain": domain}
