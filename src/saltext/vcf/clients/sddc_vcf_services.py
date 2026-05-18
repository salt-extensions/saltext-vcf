"""SDDC Manager ``/v1/vcf-services`` — the public view of the VMSP platform.

VMSP (VCF Management Services Platform) is the embedded k3s cluster
that hosts the VCF microservices (Common Services, Domain Manager,
Operations Manager, LCM, SDDC Manager UI, ...). The k3s API itself is
internal-only; SDDC Manager exposes a mediated catalog of those
services at ``/v1/vcf-services`` for status/health/version queries.

Element shape::

    {"id": "<uuid>", "name": "COMMON_SERVICES",
     "version": "9.2.0.0.25397542", "status": "UP"}
"""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/vcf-services"


def list_(opts, profile=None):
    """List every VMSP platform service."""
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, service_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{service_id}", profile=profile)


def get_or_none(opts, service_id, profile=None):
    try:
        return get(opts, service_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_by_name(opts, name, profile=None):
    """Look up a VMSP service by its symbolic name (e.g. ``COMMON_SERVICES``).

    Returns ``None`` if no service with that name exists.
    """
    body = list_(opts, profile=profile)
    elements = body.get("elements") if isinstance(body, dict) else None
    if not elements:
        return None
    for element in elements:
        if element.get("name") == name:
            return element
    return None
