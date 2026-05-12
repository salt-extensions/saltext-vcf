"""NSX QoS profile (Policy API /infra/qos-profiles).

A QoS profile binds CoS / DSCP / shaper config and can be attached to a
segment or virtual interface.
"""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/qos-profiles"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, qos_profile, profile=None):
    return nsx.api_get(opts, f"{PATH}/{qos_profile}", profile=profile)


def get_or_none(opts, qos_profile, profile=None):
    try:
        return get(opts, qos_profile, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, qos_profile, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", qos_profile)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{qos_profile}", body=body, profile=profile)


def delete(opts, qos_profile, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{qos_profile}", profile=profile)
