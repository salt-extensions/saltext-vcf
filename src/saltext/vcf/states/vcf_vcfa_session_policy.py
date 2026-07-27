"""State module for the VCFA CSP session policy.

Idempotent state that enforces the 912-controls session-policy
defaults (max auth failures 15, inactive timeout 1800s). Reads the
current policy, diffs the requested fields, and only issues a PUT
when a field is out of compliance.

Example:

.. code-block:: yaml

    vcfa-session-hardening:
      vcf_vcfa_session_policy.configured:
        - name: org-1
        - max_auth_failures: 15
        - inactive_timeout: 1800
"""

from saltext.vcf.clients import vcfa_session_policy as c

__virtualname__ = "vcf_vcfa_session_policy"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def configured(
    name,
    max_auth_failures=15,
    inactive_timeout=1800,
    session_timeout=None,
    path=None,
    profile=None,
):
    """Ensure org *name* has the requested session-policy values.

    Defaults match the 912-controls hardening baseline
    (``max_auth_failures=15``, ``inactive_timeout=1800``). Set either
    to ``None`` to skip enforcement for that field.
    """
    ret = _ret(name)
    current = c.session_policy_get(__opts__, name, path=path, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = (
            f"session policy resource not found for org {name!r}; "
            f"this VCFA build may expose it on a different path (pass path=...)"
        )
        return ret

    desired = {}
    if max_auth_failures is not None:
        desired["maxAuthFailures"] = int(max_auth_failures)
    if inactive_timeout is not None:
        desired["inactiveTimeoutSeconds"] = int(inactive_timeout)
    if session_timeout is not None:
        desired["sessionTimeoutSeconds"] = int(session_timeout)

    changes = {}
    for key, want in desired.items():
        have = current.get(key)
        if have != want:
            changes[key] = {"old": have, "new": want}

    if not changes:
        ret["comment"] = f"session policy for org {name} already compliant"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"session policy for org {name} would be updated"
        ret["changes"] = changes
        return ret

    c.session_policy_set(
        __opts__,
        name,
        max_auth_failures=max_auth_failures,
        inactive_timeout=inactive_timeout,
        session_timeout=session_timeout,
        path=path,
        profile=profile,
    )
    ret["changes"] = changes
    ret["comment"] = f"session policy for org {name} updated"
    return ret
