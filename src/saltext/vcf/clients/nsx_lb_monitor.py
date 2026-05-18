"""NSX Load Balancer monitor profiles (Policy API /infra/lb-monitor-profiles).

Monitor profiles describe how the LB health-checks pool members (TCP/HTTP/HTTPS/UDP/ICMP).
"""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/lb-monitor-profiles"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, monitor, profile=None):
    return nsx.api_get(opts, f"{PATH}/{monitor}", profile=profile)


def get_or_none(opts, monitor, profile=None):
    try:
        return get(opts, monitor, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, monitor, resource_type, profile=None, **spec):
    """*resource_type* is one of ``LBHttpMonitorProfile``, ``LBHttpsMonitorProfile``,
    ``LBTcpMonitorProfile``, ``LBUdpMonitorProfile``, ``LBIcmpMonitorProfile``,
    ``LBPassiveMonitorProfile``.
    """
    body = {
        "resource_type": resource_type,
        "display_name": spec.pop("display_name", monitor),
    }
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{monitor}", body=body, profile=profile)


def delete(opts, monitor, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{monitor}", profile=profile)
