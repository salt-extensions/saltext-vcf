"""State module for auditing SDDC Manager local application accounts.

Retrieves the list of local accounts from the SDDC Manager REST API
(``/v1/users/local-accounts``) and flags any account whose username is
not in the expected allow-list.

This control is **non-remediable** (audit-only): local accounts in SDDC
Manager are managed by the appliance lifecycle process and cannot be
safely added or removed by compliance automation.

.. note::

    This state audits **application-level** local accounts exposed by the
    SDDC Manager REST API.  It is the remote equivalent of the
    ``/etc/passwd`` inventory control in the mops config-modules framework.

.. code-block:: yaml

    # /srv/salt/sddc_accounts_audit.sls
    sddc-local-accounts:
      vcf_sddc_manager_local_accounts.audited:
        - expected_usernames:
            - vcf
            - svc-lcm
            - svc-nsxt

Example salt CLI::

    salt 'VCF-PROXY-MINION_*' state.single \\
      vcf_sddc_manager_local_accounts.audited \\
      name="sddc-accounts-check" \\
      test=True
"""

from saltext.vcf.clients import sddc_manager_local_accounts as r

__virtualname__ = "vcf_sddc_manager_local_accounts"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def audited(name, expected_usernames=None, profile=None):
    """Ensure no unexpected local accounts exist on SDDC Manager.

    When *expected_usernames* is provided, any account whose ``username``
    is not in that list is reported as unexpected.  When omitted, the state
    succeeds and reports the full account inventory (discovery mode).

    :param name: Descriptive identifier for this state.
    :param expected_usernames: Optional list of allowed account usernames.
        Any account not in this list causes ``result=False``.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.

    :return: Standard Salt state return dict.
        ``result=True``  — all accounts are in the expected list (or no list provided).
        ``result=False`` — unexpected accounts detected (non-remediable).
        ``result=None``  — dry-run (``test=True``), would have checked.
    """
    ret = _ret(name)

    accounts = r.list_or_none(__opts__, profile=profile)  # noqa: F821
    if accounts is None:
        ret["result"] = False
        ret["comment"] = "Could not retrieve local accounts from SDDC Manager."
        return ret

    usernames = [a.get("username") or a.get("name") or str(a) for a in accounts]

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = (
            f"Would audit SDDC Manager local accounts. "
            f"Found {len(accounts)} account(s): {usernames}."
        )
        return ret

    if expected_usernames is None:
        ret["comment"] = (
            f"SDDC Manager local account inventory: {len(accounts)} account(s) found: "
            f"{usernames}. (No expected list provided — discovery mode.)"
        )
        ret["changes"] = {"accounts": usernames}
        return ret

    unexpected = [u for u in usernames if u not in expected_usernames]
    if unexpected:
        ret["result"] = False
        ret["comment"] = (
            f"Unexpected local accounts detected on SDDC Manager: {unexpected}. "
            "Operator action required to remove or authorise these accounts."
        )
    else:
        ret["comment"] = (
            f"All {len(accounts)} SDDC Manager local account(s) are in the expected list."
        )

    return ret
