"""VCF Fleet Management password administration.

VCF 9.0+ exposes a fleet-wide password manager via the ``vsp-fleet`` ingress
(typically reachable through SDDC Manager's hostname). Each "account" is a
managed credential — vCenter root, NSX admin, ESXi root, SSO admin, etc. —
and the service handles rotation, history, and on-demand retrieval across
every workload domain in the fleet.

Endpoints under ``/api/fleet-management/password-management/``:

* ``GET    /accounts``                    — list all managed accounts
* ``GET    /accounts/{key}``              — one account record
* ``GET    /accounts/{key}/password``     — retrieve the current password
* ``PUT    /accounts/{key}/password``     — set/rotate a specific password
* ``POST   /accounts/{key}/rotate``       — trigger an auto-generated rotation
* ``GET    /accounts/{key}/history``      — rotation history

Auth: Bearer JWT from SDDC Manager (``POST /v1/tokens``), shared with
:mod:`saltext.vmware.utils.sddc`.

If your fleet endpoint is on a host distinct from SDDC Manager (e.g.
``vsp-fleet.example.com``), set ``saltext.vmware.fleet`` in pillar with a
``host`` override; otherwise ``saltext.vmware.sddc_manager.host`` is used.
"""

import requests

from saltext.vmware.utils import sddc

PATH = "/api/fleet-management/password-management"


def list_accounts(opts, profile=None):
    """Return every managed credential in the fleet."""
    return sddc.api_get(opts, f"{PATH}/accounts", profile=profile)


def get_account(opts, account_key, profile=None):
    """Return one account record by key."""
    return sddc.api_get(opts, f"{PATH}/accounts/{account_key}", profile=profile)


def get_account_or_none(opts, account_key, profile=None):
    try:
        return get_account(opts, account_key, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_password(opts, account_key, profile=None):
    """Retrieve the current password for *account_key* (response shape is
    typically ``{"password": "..."}``). Treat the return value as a secret.
    """
    return sddc.api_get(opts, f"{PATH}/accounts/{account_key}/password", profile=profile)


def set_password(opts, account_key, new_password, profile=None):
    """Set the password for *account_key* to *new_password* (rotation with
    an operator-supplied value). Returns the updated account record.
    """
    return sddc.api_put(
        opts,
        f"{PATH}/accounts/{account_key}/password",
        body={"password": new_password},
        profile=profile,
    )


def rotate(opts, account_key, profile=None):
    """Trigger an auto-generated rotation for *account_key*. Returns the
    task / account record (response shape is service-version-dependent).
    """
    return sddc.api_post(opts, f"{PATH}/accounts/{account_key}/rotate", profile=profile)


def history(opts, account_key, profile=None):
    """Return rotation history for *account_key*."""
    return sddc.api_get(opts, f"{PATH}/accounts/{account_key}/history", profile=profile)
