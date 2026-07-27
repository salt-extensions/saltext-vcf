"""State module for VMSP NTP configuration.

Reads and optionally remediates the NTP servers configured on the VMSP ``vsp``
component via the VMSP REST API. This control is **remediable**.

.. code-block:: yaml

    vmsp-ntp:
      vcf_vmsp_ntp.compliant:
        - servers:
            - 10.0.0.250
            - 216.239.35.8

Example salt CLI::

    # Dry-run compliance check:
    salt -C "T@vmsp:vcf-vmsp" state.single vcf_vmsp_ntp.compliant \\
      name=vmsp-ntp servers='["10.0.0.250"]' test=True

    # Apply:
    salt -C "T@vmsp:vcf-vmsp" state.single vcf_vmsp_ntp.compliant \\
      name=vmsp-ntp servers='["10.0.0.250"]' test=False
"""

from saltext.vcf.clients import vmsp_ntp as r

__virtualname__ = "vcf_vmsp_ntp"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def compliant(name, servers=None, profile=None):
    """Ensure the VMSP NTP servers match *servers*.

    :param name: Descriptive identifier for this state.
    :param servers: Desired list of NTP server addresses.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.
    """
    ret = _ret(name)
    desired = list(servers or [])

    current = r.get(__opts__, profile=profile).get("servers", [])  # noqa: F821

    if sorted(current) == sorted(desired):
        ret["comment"] = f"VMSP NTP servers already compliant: {current}"
        return ret

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"VMSP NTP servers are {current}; would set to {desired}."
        return ret

    r.set_(__opts__, desired, profile=profile)  # noqa: F821
    ret["changes"] = {"servers": {"old": current, "new": desired}}
    ret["comment"] = f"Updated VMSP NTP servers from {current} to {desired}."
    return ret
