"""Application Virtual Networks (AVNs) via SDDC Manager (/v1/avns).

AVNs are NSX-backed networks deployed by SDDC Manager as part of a
workload domain's edge stack — used for VCF-managed app overlays.
"""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/avns"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, avn_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{avn_id}", profile=profile)


def get_or_none(opts, avn_id, profile=None):
    try:
        return get(opts, avn_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def validate(opts, spec, profile=None):
    return sddc.api_post(opts, "/v1/avn-validations", body=spec, profile=profile)


def create(opts, spec, profile=None):
    return sddc.api_post(opts, PATH, body=spec, profile=profile)
