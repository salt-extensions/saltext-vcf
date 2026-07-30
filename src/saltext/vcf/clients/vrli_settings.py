"""VCF Operations for Logs (vRLI) — appliance settings (SSH-driven).

Two 912-Controls requirements on vRLI 9.0.2.0 have **no REST surface**
on this build; both are set on the appliance itself:

* **Session inactivity timeout** — lives in Jetty's ``web.xml`` at
  ``/usr/lib/loginsight/application/etc/3rd_config/web.xml`` as
  ``<session-timeout>N</session-timeout>`` (value in *minutes*). The
  vRLI API's session ``ttl`` field mirrors this same value in seconds.
  We probed ``/api/v2/settings/*``, ``/api/v2/timeouts``,
  ``/api/v2/session-timeout`` and ``/api/v2/security/session-timeout``
  — all 404 on 9.0.2.0.25575214.

* **IPv4 DNS servers** — the read-side is REST
  (``GET /api/v2/cluster/nodes`` returns ``dnsServers`` as a
  space-separated string), but there is **no write endpoint**. DNS is
  applied by ``systemd-networkd`` from
  ``/etc/systemd/network/10-eth0.network`` (static config on the
  appliance) and reflected into ``/run/systemd/resolve/resolv.conf``
  via ``systemd-resolved``. We edit ``10-eth0.network`` and restart
  ``systemd-networkd`` + ``systemd-resolved``.

Both operations require root SSH (see the ``ssh`` sub-block in
``saltext.vcf.vrli`` pillar); the API user has no filesystem access.
"""

import logging
import re

from saltext.vcf.utils import ssh as ssh_util
from saltext.vcf.utils import vrli

log = logging.getLogger(__name__)

WEB_XML = "/usr/lib/loginsight/application/etc/3rd_config/web.xml"
NETWORKD_ETH0 = "/etc/systemd/network/10-eth0.network"

# ---------------------------------------------------------------------------
# Read helpers backed by the REST cluster API (auth'd but no filesystem)
# ---------------------------------------------------------------------------

_CLUSTER_NODES = "/api/v2/cluster/nodes"


def get_cluster_nodes(opts, profile=None):
    """Return ``/api/v2/cluster/nodes`` verbatim.

    Each node dict includes ``dnsServers`` (space-separated IPv4 +
    IPv6), ``gateway``, ``netmask``, ``ip`` — all read-only.
    """
    return vrli.api_get(opts, _CLUSTER_NODES, profile=profile).get("nodes", []) or []


def get_dns_servers(opts, profile=None):
    """Return the IPv4 DNS servers reported by the API for the primary node."""
    for node in get_cluster_nodes(opts, profile=profile):
        if node.get("isPrimary"):
            return _split_ipv4(node.get("dnsServers", ""))
    # No primary flag on a single-node deployment — take the first node.
    nodes = get_cluster_nodes(opts, profile=profile)
    if nodes:
        return _split_ipv4(nodes[0].get("dnsServers", ""))
    return []


def _split_ipv4(dns_field):
    """Extract IPv4 addresses from the space-separated ``dnsServers`` field."""
    if not dns_field:
        return []
    ipv4_re = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
    return [addr for addr in dns_field.split() if ipv4_re.match(addr)]


# ---------------------------------------------------------------------------
# Session inactivity timeout — SSH read/write on web.xml
# ---------------------------------------------------------------------------


def get_session_timeout(opts, profile=None):
    """Return the current session inactivity timeout in seconds.

    Reads ``<session-timeout>`` from ``web.xml`` (which stores minutes)
    over SSH and multiplies by 60. Requires root SSH access.
    """
    ssh_cfg = vrli.get_ssh_config(opts, profile=profile)
    rc, out, err = ssh_util.run(
        ssh_cfg, f"grep -oP '(?<=<session-timeout>)\\d+(?=</session-timeout>)' {WEB_XML}"
    )
    if rc != 0 or not out.strip():
        raise RuntimeError(
            f"failed to read session-timeout from {WEB_XML}: rc={rc} err={err.strip()!r}"
        )
    minutes = int(out.strip().splitlines()[0])
    return minutes * 60


def set_session_timeout(opts, seconds, profile=None):
    """Rewrite ``<session-timeout>`` in ``web.xml`` and restart the Jetty daemon.

    *seconds* is rounded down to whole minutes (Jetty stores minutes).
    A restart of the ``loginsight`` service is triggered because the
    web descriptor is only read at daemon startup.
    """
    minutes = max(1, int(seconds) // 60)
    ssh_cfg = vrli.get_ssh_config(opts, profile=profile)
    # sed the value in place, then restart. Use a marker-safe sed pattern.
    sed = (
        f"sed -i -E 's|<session-timeout>[0-9]+</session-timeout>|"
        f"<session-timeout>{minutes}</session-timeout>|' {WEB_XML}"
    )
    rc, _out, err = ssh_util.run(ssh_cfg, sed)
    if rc != 0:
        raise RuntimeError(
            f"failed to rewrite session-timeout in {WEB_XML}: rc={rc} err={err.strip()!r}"
        )
    # Verify.
    verify_rc, verify_out, verify_err = ssh_util.run(
        ssh_cfg, f"grep -oP '(?<=<session-timeout>)\\d+(?=</session-timeout>)' {WEB_XML}"
    )
    if verify_rc != 0 or verify_out.strip().splitlines()[0:1] != [str(minutes)]:
        raise RuntimeError(
            f"session-timeout write verification failed: rc={verify_rc} out={verify_out!r} "
            f"err={verify_err.strip()!r}"
        )
    # Restart loginsight so Jetty re-reads the descriptor. Backgrounded
    # so the SSH channel closes cleanly before the API cycles.
    ssh_util.run(ssh_cfg, "systemctl restart loginsight &", timeout=15)
    return {"session_timeout_seconds": minutes * 60, "restart_requested": True}


# ---------------------------------------------------------------------------
# IPv4 DNS — SSH read/write on the systemd-networkd unit
# ---------------------------------------------------------------------------


def _read_networkd_dns(ssh_cfg):
    """Return the current IPv4 DNS= entries from 10-eth0.network."""
    _rc, out, _err = ssh_util.run(ssh_cfg, f"grep -E '^DNS=' {NETWORKD_ETH0} || true")
    servers = []
    for line in out.splitlines():
        val = line.split("=", 1)[1].strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", val):
            servers.append(val)
    return servers


def get_dns_servers_from_appliance(opts, profile=None):
    """SSH-read of the configured IPv4 nameservers.

    Prefer :func:`get_dns_servers` (REST) for read-only queries; this
    variant is exposed for parity with :func:`set_dns_servers` and
    for verification after a write.
    """
    ssh_cfg = vrli.get_ssh_config(opts, profile=profile)
    return _read_networkd_dns(ssh_cfg)


def set_dns_servers(opts, servers, profile=None):
    """Set the IPv4 DNS servers by rewriting 10-eth0.network.

    Existing IPv6 ``DNS=`` lines (if any) are preserved; only IPv4
    entries are replaced. Applies the change with
    ``networkctl reload`` and ``systemctl restart systemd-resolved``.
    """
    for addr in servers:
        if not re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", addr):
            raise ValueError(f"not an IPv4 address: {addr!r}")

    ssh_cfg = vrli.get_ssh_config(opts, profile=profile)
    # Strip every existing IPv4 DNS= line, then append the desired set.
    # printf with shell-splat quoting is fragile — use single-quoted
    # DNS= tokens inside an ``echo`` loop instead.
    ipv4_line = r"^DNS=[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
    lines = " ".join(f"'DNS={a}'" for a in servers)
    cmd = (
        f"cp {NETWORKD_ETH0} {NETWORKD_ETH0}.bak && "
        f"sed -i -E '/{ipv4_line}/d' {NETWORKD_ETH0} && "
        f'for l in {lines}; do echo "$l" >> {NETWORKD_ETH0}; done && '
        f"networkctl reload && systemctl restart systemd-resolved"
    )
    rc, out, err = ssh_util.run(ssh_cfg, cmd, timeout=60)
    if rc != 0:
        raise RuntimeError(
            f"failed to rewrite DNS in {NETWORKD_ETH0}: rc={rc} out={out.strip()!r} "
            f"err={err.strip()!r}"
        )
    return {"dns_servers": list(servers), "applied": True}
