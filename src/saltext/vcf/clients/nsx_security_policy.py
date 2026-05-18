"""NSX security policies (Policy API /infra/domains/{d}/security-policies)."""

import requests

from saltext.vcf.utils import nsx


def _base(domain="default"):
    return f"/policy/api/v1/infra/domains/{domain}/security-policies"


def list_(opts, domain="default", profile=None):
    return nsx.api_get(opts, _base(domain), profile=profile)


def get(opts, policy, domain="default", profile=None):
    return nsx.api_get(opts, f"{_base(domain)}/{policy}", profile=profile)


def get_or_none(opts, policy, domain="default", profile=None):
    try:
        return get(opts, policy, domain=domain, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, policy, domain="default", profile=None, **spec):
    """Create or update a security policy (Policy API uses PUT)."""
    body = {"display_name": spec.pop("display_name", policy)}
    body.update(spec)
    return nsx.api_put(opts, f"{_base(domain)}/{policy}", body=body, profile=profile)


def delete(opts, policy, domain="default", profile=None):
    return nsx.api_delete(opts, f"{_base(domain)}/{policy}", profile=profile)
