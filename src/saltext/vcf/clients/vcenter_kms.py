"""vCenter Key Management Service (KMS) providers — encryption key sources."""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/crypto-manager/kms/providers"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, provider_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{provider_id}", profile=profile)


def get_or_none(opts, provider_id, profile=None):
    try:
        return get(opts, provider_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, provider_spec, profile=None):
    """Create a KMS provider. *provider_spec* per the vSphere REST API."""
    return vcenter.api_post(opts, PATH, body=provider_spec, profile=profile)


def delete(opts, provider_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{provider_id}", profile=profile)
