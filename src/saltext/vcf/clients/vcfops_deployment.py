"""VCF Operations — appliance/node deployment status.

The node-status endpoint reports the running mode (``ONLINE``,
``OFFLINE``, ``MAINTENANCE``, ...), system clock, and high-level
appliance state. Pairs naturally with ``versions`` for a one-shot
"is the Ops appliance healthy" health probe.
"""

import requests

from saltext.vcf.utils import vcfops

_NODE_STATUS = "/suite-api/api/deployment/node/status"
_APPLICATIONS = "/suite-api/api/applications"


def node_status(opts, profile=None):
    return vcfops.api_get(opts, _NODE_STATUS, profile=profile)


def applications_list(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _APPLICATIONS, params={"page": page, "pageSize": page_size})


def applications_get(opts, app_id):
    return vcfops.api_get(opts, f"{_APPLICATIONS}/{app_id}")


def applications_get_or_none(opts, app_id):
    try:
        return applications_get(opts, app_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
