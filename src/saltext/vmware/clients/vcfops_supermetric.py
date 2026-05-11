"""VCF Operations — super metrics (formula-defined derived metrics)."""

import requests

from saltext.vmware.utils import vcfops

_PATH = "/suite-api/api/supermetrics"


def list_(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _PATH, params={"page": page, "pageSize": page_size})


def get(opts, supermetric_id):
    return vcfops.api_get(opts, f"{_PATH}/{supermetric_id}")


def get_or_none(opts, supermetric_id):
    try:
        return get(opts, supermetric_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, supermetric_spec):
    """Create a super metric.

    *supermetric_spec* example::

        {"name": "rolling-avg-cpu",
         "formula": "avg(${this, metric=cpu|usage_average})",
         "description": "..."}
    """
    return vcfops.api_post(opts, _PATH, body=supermetric_spec)


def update(opts, supermetric_id, supermetric_spec):
    return vcfops.api_put(opts, f"{_PATH}/{supermetric_id}", body=supermetric_spec)


def delete(opts, supermetric_id):
    return vcfops.api_delete(opts, f"{_PATH}/{supermetric_id}")
