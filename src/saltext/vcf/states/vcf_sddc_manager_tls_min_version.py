"""State module for SDDC Manager TLS minimum version compliance.

Probes the SDDC Manager HTTPS listener from the cloud proxy using
``openssl s_client`` and asserts that no TLS version older than the
desired minimum is accepted.

This control is **non-remediable**: changing the TLS minimum version
requires modifying the nginx configuration on the appliance, which has
no runtime API in SDDC Manager 9.x.

.. code-block:: yaml

    # /srv/salt/sddc_tls_compliance.sls
    sddc-tls-min-version:
      vcf_sddc_manager_tls_min_version.compliant:
        - min_version: "1.2"

Example salt CLI::

    salt 'VCF-PROXY-MINION_*' state.single \\
      vcf_sddc_manager_tls_min_version.compliant \\
      name="sddc-tls-check" \\
      min_version="1.2" \\
      test=True
"""

from saltext.vcf.clients import sddc_manager_tls as r

__virtualname__ = "vcf_sddc_manager_tls_min_version"

_VERSION_ORDER = ["1.0", "1.1", "1.2", "1.3"]


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def compliant(name, min_version="1.2", profile=None):
    """Ensure the SDDC Manager listener rejects TLS versions older than *min_version*.

    :param name: Descriptive identifier for this state (used in output).
    :param min_version: Minimum acceptable TLS version string.
        One of ``"1.0"``, ``"1.1"``, ``"1.2"``, ``"1.3"``.
        Defaults to ``"1.2"``.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.

    :return: Standard Salt state return dict.
        ``result=True``  — no version older than *min_version* is accepted.
        ``result=False`` — a version older than *min_version* is accepted
        (non-remediable; operator action required).
        ``result=None``  — dry-run (``test=True``), would have checked.
    """
    ret = _ret(name)

    state = r.get_tls_min_version(__opts__, profile=profile)  # noqa: F821
    actual_min = state.get("min_version")
    supported = state.get("supported_versions", [])

    if actual_min is None:
        ret["result"] = False
        ret["comment"] = (
            "Could not negotiate any TLS version with SDDC Manager. "
            "Verify that the listener is running and reachable."
        )
        return ret

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = (
            f"Would check TLS minimum version on SDDC Manager. "
            f"Detected min={actual_min}, supported={supported}."
        )
        return ret

    desired_idx = _VERSION_ORDER.index(min_version) if min_version in _VERSION_ORDER else 2
    actual_idx = _VERSION_ORDER.index(actual_min) if actual_min in _VERSION_ORDER else 0

    if actual_idx < desired_idx:
        ret["result"] = False
        ret["comment"] = (
            f"SDDC Manager accepts TLS {actual_min}, which is older than the "
            f"required minimum {min_version}. Supported: {supported}. "
            "Remediation requires manual nginx configuration change."
        )
    else:
        ret["comment"] = (
            f"SDDC Manager TLS minimum version is {actual_min} "
            f"(required >= {min_version}). Supported: {supported}."
        )

    return ret
