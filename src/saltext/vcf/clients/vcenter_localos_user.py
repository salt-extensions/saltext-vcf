"""vCenter Server Appliance (VAMI) local OS user accounts.

These are OS-level accounts on the appliance itself (used for SSH/console
login), managed via the appliance management API
(``com.vmware.appliance.local_accounts`` / ``/api/appliance/local-accounts``)
-- distinct from vCenter SSO users (:mod:`clients.vcenter_sso`) and from
ESXi host-level accounts.
"""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/appliance/local-accounts"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, username, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{username}", profile=profile)


def get_or_none(opts, username, profile=None):
    try:
        return get(opts, username, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, username, password, roles, profile=None, **spec):
    """Create a local OS account.

    *roles* is a list drawn from ``operator``, ``admin``, ``superAdmin``.
    Extra fields (``email``, ``full_name``, ``enabled``, ...) pass through
    in *spec*.
    """
    body = {"password": password, "roles": list(roles)}
    body.update(spec)
    return vcenter.api_post(opts, f"{PATH}/{username}", body=body, profile=profile)


def update(opts, username, profile=None, **spec):
    """Update fields on an existing account (``roles``, ``email``,
    ``full_name``, ``enabled``, ...).

    To change the password, pass both ``password`` and ``old_password`` --
    the API has no other way to rotate it without deleting and recreating
    the account (which destroys its home directory).
    """
    return vcenter.api_patch(opts, f"{PATH}/{username}", body=spec, profile=profile)


def delete(opts, username, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{username}", profile=profile)
