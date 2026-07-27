"""VCF Automation — org session policy (CSP gateway).

The CSP identity gateway on the VCFA appliance exposes an org-scoped
session-policy resource used to satisfy the 912-controls hardening
requirements for interactive UI/CLI sessions:

* **Max auth failures** — number of failed logins before the account
  lock kicks in (baseline: ``5``, hardening default: ``15``).
* **Inactive timeout** — idle session lifetime in seconds
  (baseline / hardening default: ``1800`` = 30 minutes).

Endpoints (documented under
``/csp/gateway/am/api``; the ``orgId`` scope mirrors the pattern used
by :mod:`saltext.vcf.clients.vcfa_iam`)::

    GET    /csp/gateway/am/api/orgs/{orgId}/session-policy
    PUT    /csp/gateway/am/api/orgs/{orgId}/session-policy

Not every VCFA build exposes this resource under the same path — some
older Aria Automation snapshots use
``/csp/gateway/portal/api/orgs/{orgId}/session-timeout`` instead. The
:func:`session_policy_get` / :func:`session_policy_set` helpers hit
the CSP ``am`` path first and callers can override via ``path=`` if a
specific deployment surfaces the resource elsewhere.

Field names (per the CSP schema):

* ``maxAuthFailures`` — int, positive
* ``inactiveTimeoutSeconds`` — int, positive
* ``sessionTimeoutSeconds`` — int, optional (absolute max session)
"""

import requests

from saltext.vcf.utils import vcfa

_ORGS = "/csp/gateway/am/api/orgs"


def _default_path(org_id):
    return f"{_ORGS}/{org_id}/session-policy"


def session_policy_get(opts, org_id, *, path=None, profile=None):
    """Return the current session policy for *org_id*.

    Returns ``None`` on 404 (the appliance does not expose this
    resource on the requested path — try an alternate ``path=``).
    """
    endpoint = path or _default_path(org_id)
    try:
        return vcfa.api_get(opts, endpoint, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def session_policy_set(
    opts,
    org_id,
    *,
    max_auth_failures=None,
    inactive_timeout=None,
    session_timeout=None,
    path=None,
    profile=None,
):
    """PUT a new session policy, merging over the existing one.

    Only the fields you name are overwritten. Any of *max_auth_failures*,
    *inactive_timeout*, *session_timeout* may be ``None`` to leave that
    field untouched.
    """
    if max_auth_failures is None and inactive_timeout is None and session_timeout is None:
        raise ValueError(
            "session_policy_set: at least one of max_auth_failures, "
            "inactive_timeout, session_timeout is required"
        )
    endpoint = path or _default_path(org_id)
    current = session_policy_get(opts, org_id, path=endpoint, profile=profile) or {}
    body = dict(current)
    if max_auth_failures is not None:
        body["maxAuthFailures"] = int(max_auth_failures)
    if inactive_timeout is not None:
        body["inactiveTimeoutSeconds"] = int(inactive_timeout)
    if session_timeout is not None:
        body["sessionTimeoutSeconds"] = int(session_timeout)
    return vcfa.api_put(opts, endpoint, body=body, profile=profile)
