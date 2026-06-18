"""State module for SDDC Manager local account password policy.

Reads and optionally remediates the password expiration policy via the
SDDC Manager REST API (``/v1/users/local-accounts/password-policy``).

Unlike the TLS and local-accounts states, this control **is remediable**:
the API supports both GET and PUT, allowing the salt state to enforce a
maximum password age automatically.

.. code-block:: yaml

    # /srv/salt/sddc_password_policy.sls

    # Enforce max 90-day expiry (remediable):
    sddc-password-expiry:
      vcf_sddc_manager_password_policy.within_max_age:
        - max_days: 90

    # Assert exact policy (non-remediable audit):
    sddc-password-policy-audit:
      vcf_sddc_manager_password_policy.present:
        - passwordExpirationDays: 90
        - minimumLength: 15

Example salt CLI::

    # Dry-run compliance check:
    salt 'VCF-PROXY-MINION_*' state.single \\
      vcf_sddc_manager_password_policy.within_max_age \\
      name="sddc-password-check" \\
      max_days=120 \\
      test=True

    # Apply (enforce max 90 days):
    salt 'VCF-PROXY-MINION_*' state.single \\
      vcf_sddc_manager_password_policy.within_max_age \\
      name="sddc-password-enforce" \\
      max_days=90 \\
      test=False
"""

from saltext.vcf.clients import sddc_manager_password_policy as r

__virtualname__ = "vcf_sddc_manager_password_policy"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def within_max_age(name, max_days=120, profile=None):
    """Ensure local account passwords expire within *max_days* days.

    If the current ``passwordExpirationDays`` value exceeds *max_days* the
    state remediates by setting ``passwordExpirationDays`` to *max_days*
    (all other policy fields are left unchanged).

    :param name: Descriptive identifier for this state.
    :param max_days: Maximum allowed password expiration age in days.
        Defaults to ``120``.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.

    :return: Standard Salt state return dict.
        ``result=True``  — current value is within the limit (or was remediated).
        ``result=False`` — remediation failed.
        ``result=None``  — dry-run (``test=True``), would have checked / changed.
    """
    ret = _ret(name)

    policy = r.get(__opts__, profile=profile)  # noqa: F821
    current_days = policy.get("passwordExpirationDays")

    if current_days is None:
        ret["result"] = False
        ret["comment"] = (
            "Could not read passwordExpirationDays from SDDC Manager password policy."
        )
        return ret

    if current_days <= max_days:
        ret["comment"] = (
            f"SDDC Manager passwordExpirationDays is {current_days} "
            f"(within the {max_days}-day limit)."
        )
        return ret

    # Non-compliant — remediate unless test mode.
    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = (
            f"SDDC Manager passwordExpirationDays is {current_days}, "
            f"which exceeds the {max_days}-day limit. "
            f"Would update to {max_days}."
        )
        return ret

    updated_policy = dict(policy)
    updated_policy["passwordExpirationDays"] = max_days
    r.set_(__opts__, updated_policy, profile=profile)  # noqa: F821

    ret["changes"] = {
        "passwordExpirationDays": {"old": current_days, "new": max_days}
    }
    ret["comment"] = (
        f"Updated SDDC Manager passwordExpirationDays from {current_days} to {max_days}."
    )
    return ret


def present(name, profile=None, **desired):
    """Assert that specific password policy fields match desired values.

    Any keyword argument beyond *name* and *profile* is treated as a
    desired policy field (e.g. ``passwordExpirationDays=90``,
    ``minimumLength=15``).  This state is **non-remediable** — it reports
    mismatches but does not apply changes.

    :param name: Descriptive identifier for this state.
    :param profile: Optional named profile key.
    :param desired: Keyword arguments mapping policy field names to desired values.

    :return: Standard Salt state return dict.
    """
    ret = _ret(name)

    policy = r.get(__opts__, profile=profile)  # noqa: F821

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = (
            f"Would check SDDC Manager password policy fields: {list(desired.keys())}."
        )
        return ret

    mismatches = {
        field: {"desired": val, "actual": policy.get(field)}
        for field, val in desired.items()
        if policy.get(field) != val
    }

    if mismatches:
        ret["result"] = False
        ret["comment"] = (
            "SDDC Manager password policy fields do not match desired values: "
            + "; ".join(
                f"{f}: got {v['actual']!r}, want {v['desired']!r}"
                for f, v in mismatches.items()
            )
        )
    else:
        ret["comment"] = (
            f"SDDC Manager password policy matches all desired values: "
            f"{list(desired.keys())}."
        )

    return ret
