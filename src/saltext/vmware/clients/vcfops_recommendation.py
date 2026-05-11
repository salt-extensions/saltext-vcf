"""VCF Operations — recommendation catalog.

A recommendation is the action a user can take to clear an alert
(e.g. "Increase memory for VM <foo>"). The lab has 891 recommendation
definitions; the catalog is browse-only — instances are referenced
inline from active alerts.
"""

import requests

from saltext.vmware.utils import vcfops

_PATH = "/suite-api/api/recommendations"


def list_(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _PATH, params={"page": page, "pageSize": page_size})


def get(opts, recommendation_id):
    return vcfops.api_get(opts, f"{_PATH}/{recommendation_id}")


def get_or_none(opts, recommendation_id):
    try:
        return get(opts, recommendation_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
