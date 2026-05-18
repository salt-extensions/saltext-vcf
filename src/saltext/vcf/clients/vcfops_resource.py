"""VCF Operations — managed resources (/suite-api/api/resources)."""

import requests

from saltext.vcf.utils import vcfops

PATH = "/suite-api/api/resources"


def list_(opts, page=0, page_size=1000, **filters):
    """Return paginated resources. *filters* maps to suite-api query params."""
    params = {"page": page, "pageSize": page_size}
    params.update(filters)
    return vcfops.api_get(opts, PATH, params=params)


def get(opts, resource_id):
    return vcfops.api_get(opts, f"{PATH}/{resource_id}")


def get_or_none(opts, resource_id):
    try:
        return get(opts, resource_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def relationships(opts, resource_id, **filters):
    return vcfops.api_get(opts, f"{PATH}/{resource_id}/relationships", params=filters or None)


def stats(opts, resource_id, **filters):
    return vcfops.api_get(opts, f"{PATH}/{resource_id}/stats", params=filters or None)
