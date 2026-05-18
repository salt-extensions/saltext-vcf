"""NSX Load Balancer application profiles (Policy API /infra/lb-app-profiles).

App profiles are L7 (HTTP/TCP/UDP) settings attached to virtual servers.
"""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/lb-app-profiles"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, app_profile, profile=None):
    return nsx.api_get(opts, f"{PATH}/{app_profile}", profile=profile)


def get_or_none(opts, app_profile, profile=None):
    try:
        return get(opts, app_profile, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, app_profile, resource_type, profile=None, **spec):
    """*resource_type* is one of ``LBHttpProfile``, ``LBFastTcpProfile``, ``LBFastUdpProfile``."""
    body = {
        "resource_type": resource_type,
        "display_name": spec.pop("display_name", app_profile),
    }
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{app_profile}", body=body, profile=profile)


def delete(opts, app_profile, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{app_profile}", profile=profile)
