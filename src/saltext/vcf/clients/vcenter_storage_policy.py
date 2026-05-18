"""Client for vCenter Storage Policy-Based Management (/api/vcenter/storage/policies).

Note: the vSphere REST SPBM API has no per-policy GET path. Policies are a
synthesized view of profiles from multiple underlying sources (built-in
VMC profiles, vSAN, vVol, user-authored) and are exposed only as an
enumerable, filterable list. :func:`get` is implemented in terms of the
filter query parameter (``?policies=<id>``) which returns a single-element
list when the id matches.
"""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/storage/policies"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, policy, profile=None):
    """Return the single policy with id *policy*.

    Implemented via the filter query parameter since the SPBM REST API has
    no per-id GET path. Raises :class:`requests.HTTPError` 404 when the
    policy is unknown.
    """
    result = vcenter.api_get(opts, PATH, params={"policies": policy}, profile=profile)
    if isinstance(result, list) and result:
        return result[0]
    resp = requests.Response()
    resp.status_code = 404
    raise requests.HTTPError("storage policy not found", response=resp)


def get_or_none(opts, policy, profile=None):
    try:
        return get(opts, policy, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
