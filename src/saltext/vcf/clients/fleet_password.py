"""VCF Fleet Management password administration via SDDC Manager.

SDDC Manager exposes the fleet credential store at ``/v1/credentials``. Each
"credential" is a managed account — vCenter root, NSX admin, ESXi root, SSO
admin, etc. — and the service handles rotation, history, and on-demand
retrieval across every workload domain in the fleet.

Endpoints (all on the SDDC Manager host):

* ``GET    /v1/credentials``                  — list all managed credentials
* ``GET    /v1/credentials/{id}``             — one credential record
* ``GET    /v1/credentials/{id}/password-history`` — rotation history
* ``POST   /v1/credentials/operations``       — rotate / update one or more
  credentials (request body specifies ``operationType``: ``ROTATE`` or
  ``UPDATE`` and lists affected ``elements``)
* ``GET    /v1/credentials/tasks/{task_id}``  — track an operation

Auth: Bearer JWT from SDDC Manager (``POST /v1/tokens``), shared with
:mod:`saltext.vcf.utils.sddc`.
"""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/credentials"


def list_accounts(opts, profile=None):
    """Return every managed credential in the fleet."""
    return sddc.api_get(opts, PATH, profile=profile)


def get_account(opts, account_key, profile=None):
    """Return one credential record by id."""
    return sddc.api_get(opts, f"{PATH}/{account_key}", profile=profile)


def get_account_or_none(opts, account_key, profile=None):
    try:
        return get_account(opts, account_key, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_password(opts, account_key, profile=None):
    """Return the credential record (the encrypted password lives in
    ``response["password"]``). Treat the return value as a secret.
    """
    return sddc.api_get(opts, f"{PATH}/{account_key}", profile=profile)


def set_password(opts, account_key, new_password, profile=None):
    """Update the password for *account_key* via the operations endpoint."""
    body = {
        "operationType": "UPDATE",
        "elements": [
            {"resourceCredentials": [{"credentialId": account_key, "password": new_password}]}
        ],
    }
    return sddc.api_post(opts, f"{PATH}/operations", body=body, profile=profile)


def rotate(opts, account_key, profile=None):
    """Trigger an auto-generated rotation for *account_key*."""
    body = {
        "operationType": "ROTATE",
        "elements": [{"resourceCredentials": [{"credentialId": account_key}]}],
    }
    return sddc.api_post(opts, f"{PATH}/operations", body=body, profile=profile)


def history(opts, account_key, profile=None):
    """Return rotation history for *account_key*."""
    return sddc.api_get(opts, f"{PATH}/{account_key}/password-history", profile=profile)
