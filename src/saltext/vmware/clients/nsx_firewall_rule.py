"""NSX distributed firewall rules (per-security-policy children)."""

import requests

from saltext.vmware.utils import nsx


def _base(domain, policy):
    return f"/policy/api/v1/infra/domains/{domain}/security-policies/{policy}/rules"


def list_(opts, policy, domain="default", profile=None):
    return nsx.api_get(opts, _base(domain, policy), profile=profile)


def get(opts, rule, policy, domain="default", profile=None):
    return nsx.api_get(opts, f"{_base(domain, policy)}/{rule}", profile=profile)


def get_or_none(opts, rule, policy, domain="default", profile=None):
    try:
        return get(opts, rule, policy, domain=domain, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, rule, policy, domain="default", profile=None, **spec):
    """Create or update a firewall rule (PUT).

    Common keys: ``display_name``, ``source_groups``, ``destination_groups``,
    ``services``, ``profiles``, ``scope``, ``action`` (ALLOW/DROP/REJECT),
    ``ip_protocol``, ``direction`` (IN/OUT/IN_OUT).
    """
    body = {"display_name": spec.pop("display_name", rule)}
    body.update(spec)
    return nsx.api_put(opts, f"{_base(domain, policy)}/{rule}", body=body, profile=profile)


def delete(opts, rule, policy, domain="default", profile=None):
    return nsx.api_delete(opts, f"{_base(domain, policy)}/{rule}", profile=profile)
