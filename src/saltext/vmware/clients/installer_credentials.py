"""VCF Installer credential management.

The installer holds passwords for every component it deploys (vCenter root,
NSX admin, SDDC Manager admin, etc.). Rotation is done before handoff to
SDDC Manager.
"""

import requests

from saltext.vmware.utils import installer


def list_(opts, profile=None):
    """Return every managed credential."""
    return installer.api_get(opts, "/v1/system/security/passwords", profile=profile)


def get(opts, password_id, profile=None):
    return installer.api_get(opts, f"/v1/system/security/passwords/{password_id}", profile=profile)


def get_or_none(opts, password_id, profile=None):
    try:
        return get(opts, password_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def rotate(opts, password_id, new_password, profile=None):
    """Rotate a managed credential. Returns the updated record."""
    return installer.api_patch(
        opts,
        f"/v1/system/security/passwords/{password_id}",
        body={"password": new_password},
        profile=profile,
    )
