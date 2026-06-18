"""Local accounts client for SDDC Manager (/v1/users/local-accounts).

Returns the application-level local accounts managed by SDDC Manager.
This is the remote equivalent of reading ``/etc/passwd`` on the appliance —
it reflects SDDC Manager application accounts rather than raw OS accounts.

Config is read from Salt opts/pillar under ``saltext.vcf.sddc_manager``:

.. code-block:: yaml

    saltext.vcf:
      sddc_manager:
        host: sddc-manager.example.test
        username: administrator@vsphere.local
        password: secret
        verify_ssl: false
"""

import requests

from saltext.vcf.utils import sddc

_PATH = "/v1/users/local-accounts"


def list_(opts, profile=None):
    """Return all local accounts from SDDC Manager.

    :param opts: Salt opts / pillar dict.
    :param profile: Optional named profile key.
    :return: List of local account dicts from the API.
    """
    result = sddc.api_get(opts, _PATH, profile=profile)
    return result.get("elements", result) if isinstance(result, dict) else result


def list_or_none(opts, profile=None):
    """Return local accounts or ``None`` on 404 / service unavailable."""
    try:
        return list_(opts, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (404, 503):
            return None
        raise
