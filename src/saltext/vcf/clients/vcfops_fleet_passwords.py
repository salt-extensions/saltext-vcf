"""VCF Operations — fleet password management (VCF 9.x).

The VCF Operations 9.1 ``suite-api`` exposes a fleet-wide password manager
at ``/suite-api/api/fleet-management/password-management``. Each managed
**password account** (vCenter root, NSX admin, ESXi root, SSO admin, …)
is identified by an opaque ``passwordAccountKey``; query results include
expiration metadata (``expiryDate`` as a unix-millisecond timestamp,
``status``: ``ACTIVE`` / ``EXPIRING`` / ``EXPIRED`` / ``UNKNOWN``).

Endpoints used here (all on the VCF Operations host):

* ``POST   /suite-api/api/fleet-management/password-management/accounts/query``
  — paginated list, with optional ``appliance`` / ``applianceFqdn`` /
  ``status`` / ``username`` / ``vcfDomainId`` filters; query params
  ``page``, ``pageSize``, ``sortBy``, ``sortOrder``.
* ``PUT    /suite-api/api/fleet-management/password-management/accounts/{passwordAccountKey}/password``
  — set a new password; returns a ``WorkflowRequest`` describing the
  async credential-rotation job VCF Operations kicked off.

Auth is the same VCF Operations bearer-token surface used by every other
``vcfops_*`` client (see :mod:`saltext.vcf.utils.vcfops`).

This module is the recommended way to administer fleet passwords on VCF
9.x; :mod:`saltext.vcf.clients.fleet_password` (SDDC Manager-backed) is
retained for older deployments but the SDDC password surface is being
deprecated.
"""

from datetime import datetime
from datetime import timezone

from saltext.vcf.utils import vcfops

_BASE = "/suite-api/api/fleet-management/password-management"

DEFAULT_EXPIRY_THRESHOLD_DAYS = 90


def _iso(ms):
    """Convert a unix-ms timestamp to an ISO-8601 ``Z`` string, or ``None``.

    VCF Operations reports ``0`` for accounts that never expire (most
    admin / service accounts); preserve that as ``None`` in enriched
    records so callers can distinguish "no expiry" from "expires now".
    """
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _enrich(account):
    """Return a copy of *account* with ``expiryDateIso`` added."""
    out = dict(account)
    out["expiryDateIso"] = _iso(account.get("expiryDate"))
    return out


def query_accounts(
    opts,
    *,
    appliance=None,
    appliance_fqdn=None,
    status=None,
    username=None,
    vcf_domain_id=None,
    page=0,
    page_size=10,
    sort_by=None,
    sort_order=None,
    profile=None,
):
    """Raw paginated search; returns the unmodified ``VcfPasswordAccountsResponse``.

    Most callers want :func:`list_` (walks pagination, enriches with
    ``expiryDateIso``); this is the low-level handle for clients that need
    fine-grained control over paging.
    """
    body = {}
    if appliance is not None:
        body["appliance"] = appliance
    if appliance_fqdn is not None:
        body["applianceFqdn"] = appliance_fqdn
    if status is not None:
        body["status"] = status
    if username is not None:
        body["username"] = username
    if vcf_domain_id is not None:
        body["vcfDomainId"] = vcf_domain_id
    params = {"page": page, "pageSize": page_size}
    if sort_by is not None:
        params["sortBy"] = sort_by
    if sort_order is not None:
        params["sortOrder"] = sort_order
    return vcfops.api_post(
        opts, f"{_BASE}/accounts/query", body=body, params=params, profile=profile
    )


def list_(opts, *, profile=None, page_size=100, **filters):
    """List every managed password account.

    Walks pagination and returns ``{"accounts": [...], "totalCount": N}``.
    Each account dict is enriched with ``expiryDateIso`` (the ISO-8601
    rendering of ``expiryDate`` in UTC, or ``None`` when the account
    never expires).

    *filters* accepts the same keyword filters as :func:`query_accounts`
    (``appliance``, ``appliance_fqdn``, ``status``, ``username``,
    ``vcf_domain_id``).
    """
    accounts = []
    total = 0
    page = 0
    while True:
        resp = query_accounts(opts, page=page, page_size=page_size, profile=profile, **filters)
        chunk = resp.get("vcfPasswordAccounts", []) or []
        accounts.extend(_enrich(a) for a in chunk)
        page_info = resp.get("pageInfo", {}) or {}
        total = page_info.get("totalCount", len(accounts))
        if not chunk or len(accounts) >= total:
            break
        page += 1
    return {"accounts": accounts, "totalCount": total}


def get_account(opts, password_account_key, profile=None):
    """Return the single account record matching *password_account_key*, or
    ``None`` if no account with that key is currently registered.
    """
    for acct in list_(opts, profile=profile)["accounts"]:
        if acct.get("passwordAccountKey") == password_account_key:
            return acct
    return None


def check_expiry(opts, *, threshold_days=DEFAULT_EXPIRY_THRESHOLD_DAYS, profile=None, **filters):
    """Categorize accounts into ``ok`` / ``expiring`` / ``noExpiry`` buckets.

    *threshold_days* — accounts whose ``expiryDate`` is within this many
    days of "now" land in ``expiring`` (including already-expired
    accounts, which have a negative ``daysUntilExpiry``). Default 90.

    Returns::

        {
            "ok": [...],            # daysUntilExpiry > threshold_days
            "expiring": [...],      # 0 ... threshold_days (and <0 if expired)
            "noExpiry": [...],      # expiryDate == 0 (e.g. admin accounts)
            "okCount": int,
            "expiringCount": int,
            "noExpiryCount": int,
            "totalCount": int,
            "expiryThresholdDays": threshold_days,
        }

    Each ``ok`` / ``expiring`` account is augmented with
    ``daysUntilExpiry`` (float, rounded to 1 decimal). ``noExpiry``
    entries are returned as-is.

    *filters* accepts the same keyword filters as :func:`list_`, so
    callers can scope the check to a single appliance / fqdn / domain.
    """
    listing = list_(opts, profile=profile, **filters)
    now_ms = datetime.now(tz=timezone.utc).timestamp() * 1000
    threshold_ms = threshold_days * 86400 * 1000

    ok = []
    expiring = []
    no_expiry = []
    for acct in listing["accounts"]:
        exp = acct.get("expiryDate") or 0
        if exp == 0:
            no_expiry.append(acct)
            continue
        delta = exp - now_ms
        bucketed = dict(acct, daysUntilExpiry=round(delta / 86400000, 1))
        if delta <= threshold_ms:
            expiring.append(bucketed)
        else:
            ok.append(bucketed)

    return {
        "ok": ok,
        "expiring": expiring,
        "noExpiry": no_expiry,
        "okCount": len(ok),
        "expiringCount": len(expiring),
        "noExpiryCount": len(no_expiry),
        "totalCount": listing["totalCount"],
        "expiryThresholdDays": threshold_days,
    }


def update(
    opts,
    password_account_key,
    current_password,
    new_password,
    username=None,
    profile=None,
):
    """Update the password for *password_account_key*.

    Returns the ``WorkflowRequest`` dict describing the async rotation
    job VCF Operations enqueued (``requestId``, ``state``, ``duration``,
    ``errorCause``, …). The actual rotation may take minutes; poll the
    ``requestId`` via the workflow API if you need to wait for
    completion.
    """
    body = {"currentPassword": current_password, "newPassword": new_password}
    if username is not None:
        body["userName"] = username
    return vcfops.api_put(
        opts, f"{_BASE}/accounts/{password_account_key}/password", body=body, profile=profile
    )
