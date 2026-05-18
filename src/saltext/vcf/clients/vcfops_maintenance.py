"""VCF Operations — maintenance schedules.

Maintenance schedules pause alerting (and optionally data collection)
for a set of resources during a window. Used during planned upgrades.
"""

import requests

from saltext.vcf.utils import vcfops

_PATH = "/suite-api/api/maintenanceschedules"


def list_(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _PATH, params={"page": page, "pageSize": page_size})


def get(opts, schedule_id):
    return vcfops.api_get(opts, f"{_PATH}/{schedule_id}")


def get_or_none(opts, schedule_id):
    try:
        return get(opts, schedule_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, schedule_spec):
    return vcfops.api_post(opts, _PATH, body=schedule_spec)


def update(opts, schedule_id, schedule_spec):
    return vcfops.api_put(opts, f"{_PATH}/{schedule_id}", body=schedule_spec)


def delete(opts, schedule_id):
    return vcfops.api_delete(opts, f"{_PATH}/{schedule_id}")
