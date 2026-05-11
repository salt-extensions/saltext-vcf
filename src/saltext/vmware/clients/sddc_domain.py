"""Resource layer for SDDC Manager workload domains (/v1/domains)."""

import requests

from saltext.vmware.utils import sddc

PATH = "/v1/domains"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, domain, profile=None):
    return sddc.api_get(opts, f"{PATH}/{domain}", profile=profile)


def get_or_none(opts, domain, profile=None):
    try:
        return get(opts, domain, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_by_name(opts, name, profile=None):
    body = list_(opts, profile=profile)
    for el in body.get("elements") or []:
        if el.get("name") == name:
            return el
    return None


def validate(opts, spec, profile=None):
    return sddc.api_post(opts, f"{PATH}/validations", body=spec, profile=profile)


def create(opts, spec, profile=None):
    return sddc.api_post(opts, PATH, body=spec, profile=profile)


def update(opts, domain, spec, profile=None):
    return sddc.api_patch(opts, f"{PATH}/{domain}", body=spec, profile=profile)


def delete(opts, domain, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{domain}", profile=profile)


def mark_for_deletion(opts, domain, profile=None):
    spec = {"markForDeletion": True}
    return sddc.api_patch(opts, f"{PATH}/{domain}", body=spec, profile=profile)


def list_endpoints(opts, domain, profile=None):
    return sddc.api_get(opts, f"{PATH}/{domain}/endpoints", profile=profile)
