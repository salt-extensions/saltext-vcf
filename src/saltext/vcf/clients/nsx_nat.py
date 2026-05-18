"""NSX NAT rules — per Tier-1 (or Tier-0) gateway, scoped USER or INTERNAL."""

import requests

from saltext.vcf.utils import nsx


def _t1_path(t1_id, scope="USER"):
    return f"/policy/api/v1/infra/tier-1s/{t1_id}/nat/{scope}/nat-rules"


def _t0_path(t0_id, scope="USER"):
    return f"/policy/api/v1/infra/tier-0s/{t0_id}/nat/{scope}/nat-rules"


def list_(opts, t1, scope="USER", profile=None):
    return nsx.api_get(opts, _t1_path(t1, scope), profile=profile)


def get(opts, rule, t1, scope="USER", profile=None):
    return nsx.api_get(opts, f"{_t1_path(t1, scope)}/{rule}", profile=profile)


def get_or_none(opts, rule, t1, scope="USER", profile=None):
    try:
        return get(opts, rule, t1, scope=scope, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, rule, t1, scope="USER", profile=None, **spec):
    """Create or update a NAT rule (PUT).

    Common spec fields: ``action`` (SNAT/DNAT/REFLEXIVE/NO_SNAT/NO_DNAT),
    ``source_network``, ``destination_network``, ``translated_network``,
    ``translated_ports``, ``service``.
    """
    body = {"display_name": spec.pop("display_name", rule)}
    body.update(spec)
    return nsx.api_put(opts, f"{_t1_path(t1, scope)}/{rule}", body=body, profile=profile)


def delete(opts, rule, t1, scope="USER", profile=None):
    return nsx.api_delete(opts, f"{_t1_path(t1, scope)}/{rule}", profile=profile)


# Tier-0 mirrors
def list_t0(opts, t0, scope="USER", profile=None):
    return nsx.api_get(opts, _t0_path(t0, scope), profile=profile)


def create_t0(opts, rule, t0, scope="USER", profile=None, **spec):
    body = {"display_name": spec.pop("display_name", rule)}
    body.update(spec)
    return nsx.api_put(opts, f"{_t0_path(t0, scope)}/{rule}", body=body, profile=profile)


def delete_t0(opts, rule, t0, scope="USER", profile=None):
    return nsx.api_delete(opts, f"{_t0_path(t0, scope)}/{rule}", profile=profile)
