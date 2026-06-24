"""State module for VMSP syslog configuration.

Reads and optionally remediates the syslog forwarding settings on the VMSP
``vsp`` component via the VMSP REST API. This control is **remediable**.

.. code-block:: yaml

    vmsp-syslog:
      vcf_vmsp_syslog.compliant:
        - host: syslog.example.test
        - port: 514
        - transport: tcp
        - insecure: false

Example salt CLI::

    salt -C "T@vmsp:vcf-vmsp" state.single vcf_vmsp_syslog.compliant \\
      name=vmsp-syslog host=syslog.example.test port=514 transport=tcp test=True
"""

from saltext.vcf.clients import vmsp_syslog as r

__virtualname__ = "vcf_vmsp_syslog"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def compliant(name, host=None, port=514, transport="tcp", insecure=False, cacert=None, profile=None):
    """Ensure the VMSP syslog server settings match the desired values.

    :param name: Descriptive identifier for this state.
    :param host: Desired syslog server hostname/IP.
    :param port: Desired syslog port. Defaults to ``514``.
    :param transport: Desired transport (``tcp``/``udp``/``tls``). Defaults to ``tcp``.
    :param insecure: Whether to allow an insecure TLS connection. Defaults to ``False``.
    :param cacert: Optional CA certificate for TLS transport.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.
    """
    ret = _ret(name)

    if not host:
        ret["result"] = False
        ret["comment"] = "host is required for vcf_vmsp_syslog.compliant."
        return ret

    desired = {"host": host, "port": port, "insecure": insecure, "transport": transport}
    if cacert:
        desired["cacert"] = cacert

    current = r.get(__opts__, profile=profile).get("syslog", {})  # noqa: F821

    # Compare only the fields we manage; ignore extra server-side keys.
    current_subset = {k: current.get(k) for k in desired}
    if current_subset == desired:
        ret["comment"] = f"VMSP syslog already compliant: {current_subset}"
        return ret

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"VMSP syslog is {current_subset}; would set to {desired}."
        return ret

    r.set_(  # noqa: F821
        __opts__,
        host=host,
        port=port,
        transport=transport,
        insecure=insecure,
        cacert=cacert,
        profile=profile,
    )
    ret["changes"] = {"syslog": {"old": current_subset, "new": desired}}
    ret["comment"] = f"Updated VMSP syslog from {current_subset} to {desired}."
    return ret
