"""VCF Operations — solutions / management packs."""

import requests

from saltext.vcf.utils import vcfops

_PATH = "/suite-api/api/solutions"


def list_(opts):
    return vcfops.api_get(opts, _PATH)


def get(opts, solution_id):
    return vcfops.api_get(opts, f"{_PATH}/{solution_id}")


def get_or_none(opts, solution_id):
    try:
        return get(opts, solution_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
