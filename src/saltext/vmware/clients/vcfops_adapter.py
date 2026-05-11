"""VCF Operations — adapter kinds (/suite-api/api/adapterkinds)."""

import requests

from saltext.vmware.utils import vcfops

PATH = "/suite-api/api/adapterkinds"


def list_(opts):
    return vcfops.api_get(opts, PATH)


def get(opts, kind_key):
    return vcfops.api_get(opts, f"{PATH}/{kind_key}")


def get_or_none(opts, kind_key):
    try:
        return get(opts, kind_key)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
