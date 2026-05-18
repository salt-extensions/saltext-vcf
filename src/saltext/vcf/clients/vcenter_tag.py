"""Resource layer for vCenter tags (/api/cis/tagging)."""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/cis/tagging/tag"
ASSOC_PATH = "/api/cis/tagging/tag-association"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, tag, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{tag}", profile=profile)


def get_or_none(opts, tag, profile=None):
    try:
        return get(opts, tag, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, name, category_id, description="", profile=None):
    body = {
        "name": name,
        "category_id": category_id,
        "description": description,
    }
    return vcenter.api_post(opts, PATH, body=body, profile=profile)


def update(opts, tag, spec, profile=None):
    """PATCH a tag. *spec* keys: ``name``, ``description``."""
    return vcenter.api_patch(opts, f"{PATH}/{tag}", body=dict(spec), profile=profile)


def delete(opts, tag, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{tag}", profile=profile)


def assign(opts, tag, object_type, object_id, profile=None):
    body = {"object_id": {"type": object_type, "id": object_id}}
    return vcenter.api_post(
        opts,
        f"{ASSOC_PATH}/{tag}",
        body=body,
        params={"action": "attach"},
        profile=profile,
    )


def list_assigned(opts, object_type, object_id, profile=None):
    body = {"object_id": {"type": object_type, "id": object_id}}
    return vcenter.api_post(
        opts,
        ASSOC_PATH,
        body=body,
        params={"action": "list-attached-tags"},
        profile=profile,
    )
