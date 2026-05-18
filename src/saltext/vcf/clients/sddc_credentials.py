"""Resource layer for SDDC Manager credentials (/v1/credentials)."""

from saltext.vcf.utils import sddc

PATH = "/v1/credentials"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def rotate(opts, elements, profile=None):
    body = {"operationType": "ROTATE", "elements": elements}
    return sddc.api_patch(opts, PATH, body=body, profile=profile)
