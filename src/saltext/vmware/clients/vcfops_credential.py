"""VCF Operations — stored credentials and credential kinds.

Credentials are the named secret records that adapter instances bind
to when they connect to a target (a vCenter, an NSX manager, etc.).
Credential kinds describe the fields each credential type requires
(username, password, port, etc.).
"""

import requests

from saltext.vmware.utils import vcfops

_CREDS = "/suite-api/api/credentials"
_KINDS = "/suite-api/api/credentialkinds"


def list_(opts, profile=None):
    return vcfops.api_get(opts, _CREDS, profile=profile)


def get(opts, credential_id, profile=None):
    return vcfops.api_get(opts, f"{_CREDS}/{credential_id}", profile=profile)


def get_or_none(opts, credential_id, profile=None):
    try:
        return get(opts, credential_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, credential_spec, profile=None):
    """Create a credential record.

    *credential_spec* example::

        {
            "name": "vcenter-prod",
            "adapterKindKey": "VMWARE",
            "credentialKindKey": "PRINCIPALCREDENTIAL",
            "fields": [
                {"name": "USER", "value": "administrator@vsphere.local"},
                {"name": "PASSWORD", "value": "..."}
            ]
        }
    """
    return vcfops.api_post(opts, _CREDS, body=credential_spec, profile=profile)


def update(opts, credential_id, credential_spec, profile=None):
    return vcfops.api_put(opts, f"{_CREDS}/{credential_id}", body=credential_spec, profile=profile)


def delete(opts, credential_id, profile=None):
    return vcfops.api_delete(opts, f"{_CREDS}/{credential_id}", profile=profile)


def kinds_list(opts, profile=None):
    return vcfops.api_get(opts, _KINDS, profile=profile)
