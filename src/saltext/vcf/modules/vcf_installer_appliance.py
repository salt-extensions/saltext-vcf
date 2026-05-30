"""Execution module: deploy and probe the VCF Installer appliance.

The deploy step is a one-shot OVA push onto a bare ESXi host using the
configured backend (pyVmomi by default, or ovftool for standalone ESXi).
Once it returns, the appliance's standard bringup REST flow lives
in :mod:`saltext.vcf.modules.vcf_installer_bringup`.
"""

from saltext.vcf.clients import installer_appliance as c

__virtualname__ = "vcf_installer_appliance"


def __virtual__():
    return __virtualname__


def is_reachable(host, port=443, timeout=5):
    """Return ``True`` if ``host:port`` accepts a TCP connection.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_appliance.is_reachable installer.lab.local
    """
    return c.is_appliance_reachable(host, port=int(port), timeout=int(timeout))


def wait_until_reachable(host, port=443, timeout=900, poll_interval=15):
    """Block until ``host:port`` accepts TCP. Raises on timeout.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_appliance.wait_until_reachable installer.lab.local timeout=300
    """
    c.wait_until_reachable(
        host, port=int(port), timeout=int(timeout), poll_interval=int(poll_interval)
    )
    return True


def deploy(installer_spec=None):
    """Deploy the VCF Installer OVA per *installer_spec*.

    If *installer_spec* is omitted, it is read from pillar key
    ``saltext.vcf:installer_appliance``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_appliance.deploy
    """
    spec = _resolve_spec(installer_spec)
    return c.deploy_installer(spec)


def ensure_running(installer_spec=None):
    """Idempotent deploy: skip if the appliance host is already reachable.

    Returns a dict with at least ``{"reachable": bool, "deployed": bool}``.
    On a fresh deploy, also includes the ``deploy_ova`` result keys
    (``vm_name``, ``vm_moid``, ``powered_on``, ``elapsed_sec``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_appliance.ensure_running
    """
    spec = _resolve_spec(installer_spec)
    host = spec["installer_host"]
    port = int(spec.get("installer_port", 443))
    if c.is_appliance_reachable(host, port=port):
        return {"reachable": True, "deployed": False}
    deploy_result = c.deploy_installer(spec)
    c.wait_until_reachable(
        host,
        port=port,
        timeout=int(spec.get("timeout_sec", 900)),
        poll_interval=int(spec.get("polling_interval_sec", 15)),
    )
    return {"reachable": True, "deployed": True, **deploy_result}


def _resolve_spec(installer_spec):
    if installer_spec is not None:
        return installer_spec
    pillar = __opts__.get("pillar", {})  # noqa: F821
    root = pillar.get("saltext.vcf", {}) or {}
    spec = root.get("installer_appliance")
    if not spec:
        raise KeyError(
            "no installer_spec provided and pillar 'saltext.vcf:installer_appliance' is unset"
        )
    return spec
