"""Execution module for VCF Automation org session policy.

Wraps :mod:`saltext.vcf.clients.vcfa_session_policy` so operators can
inspect / adjust the CSP session policy (max auth failures + inactive
timeout) from ``salt-call``.

CLI Example:

.. code-block:: bash

    salt '*' vcf_vcfa_session_policy.get org-1
    salt '*' vcf_vcfa_session_policy.set org-1 max_auth_failures=15 inactive_timeout=1800
"""

from saltext.vcf.clients import vcfa_session_policy as c

__virtualname__ = "vcf_vcfa_session_policy"


def __virtual__():
    return __virtualname__


def get(org_id, path=None, profile=None):
    """Return the current session policy for *org_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_session_policy.get org-1
    """
    return c.session_policy_get(__opts__, org_id, path=path, profile=profile)


def set_(
    org_id,
    max_auth_failures=None,
    inactive_timeout=None,
    session_timeout=None,
    path=None,
    profile=None,
):
    """PUT a new session policy on *org_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_session_policy.set org-1 max_auth_failures=15 inactive_timeout=1800
    """
    return c.session_policy_set(
        __opts__,
        org_id,
        max_auth_failures=max_auth_failures,
        inactive_timeout=inactive_timeout,
        session_timeout=session_timeout,
        path=path,
        profile=profile,
    )
