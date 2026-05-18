"""Resource layer for vCenter clusters (/api/vcenter/cluster)."""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/cluster"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, cluster, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{cluster}", profile=profile)


def get_or_none(opts, cluster, profile=None):
    try:
        return get(opts, cluster, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, name, datacenter=None, profile=None, **spec):
    body = {"name": name}
    if datacenter is not None:
        body["datacenter"] = datacenter
    body.update(spec)
    return vcenter.api_post(opts, PATH, body=body, profile=profile)


def delete(opts, cluster, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{cluster}", profile=profile)
