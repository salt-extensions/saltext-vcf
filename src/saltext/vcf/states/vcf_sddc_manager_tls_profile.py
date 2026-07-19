"""State module for SDDC Manager TLS cipher profile compliance.

Probes the SDDC Manager HTTPS listener from the cloud proxy using
``openssl s_client`` to detect the active cipher profile and asserts
it matches the desired value.

Detected profiles:

* ``NIST_2024_TLS_13_ONLY`` — TLS 1.2 rejected, TLS 1.3 accepted.
* ``NIST_2024``             — TLS 1.2+1.3 accepted, GCM-only (CBC rejected).
* ``COMPATIBLE``             — TLS 1.2+1.3 accepted, CBC ciphers allowed.
* ``MANUAL``                 — Any other configuration.

This control is **non-remediable**: changing the cipher profile requires
modifying the nginx configuration on the appliance.

.. code-block:: yaml

    # /srv/salt/sddc_tls_compliance.sls
    sddc-tls-profile:
      vcf_sddc_manager_tls_profile.compliant:
        - profile_name: "NIST_2024"

Example salt CLI::

    salt 'VCF-PROXY-MINION_*' state.single \\
      vcf_sddc_manager_tls_profile.compliant \\
      name="sddc-profile-check" \\
      profile_name="NIST_2024" \\
      test=True
"""

from saltext.vcf.clients import sddc_manager_tls as r

__virtualname__ = "vcf_sddc_manager_tls_profile"

VALID_PROFILES = ("NIST_2024", "NIST_2024_TLS_13_ONLY", "COMPATIBLE", "MANUAL")


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def compliant(name, profile_name="NIST_2024", profile=None):
    """Ensure the SDDC Manager listener uses the specified TLS cipher profile.

    :param name: Descriptive identifier for this state.
    :param profile_name: Desired cipher profile name.
        One of ``"NIST_2024"``, ``"NIST_2024_TLS_13_ONLY"``,
        ``"COMPATIBLE"``, ``"MANUAL"``. Defaults to ``"NIST_2024"``.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.

    :return: Standard Salt state return dict.
        ``result=True``  — detected profile matches *profile_name*.
        ``result=False`` — mismatch detected (non-remediable).
        ``result=None``  — dry-run (``test=True``), would have checked.
    """
    ret = _ret(name)

    state = r.get_tls_profile(__opts__, profile=profile)  # noqa: F821
    detected = state.get("profile", "MANUAL")

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = (
            f"Would check TLS cipher profile on SDDC Manager. "
            f"Detected profile: {detected}."
        )
        return ret

    if detected == profile_name:
        ret["comment"] = f"SDDC Manager TLS cipher profile is {detected} (desired: {profile_name})."
    else:
        ret["result"] = False
        ret["comment"] = (
            f"SDDC Manager TLS cipher profile is {detected}, "
            f"but {profile_name} is required. "
            "Remediation requires manual nginx configuration change."
        )

    return ret
