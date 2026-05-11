"""VCF Operations — async task status."""

import requests

from saltext.vmware.utils import vcfops

_PATH = "/suite-api/api/tasks"


def list_(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _PATH, params={"page": page, "pageSize": page_size})


def get(opts, task_id):
    return vcfops.api_get(opts, f"{_PATH}/{task_id}")


def get_or_none(opts, task_id):
    try:
        return get(opts, task_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
