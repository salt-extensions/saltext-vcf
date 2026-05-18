"""Resource layer for vCenter tag categories (/api/cis/tagging/category).

A tag category groups related tags and constrains:

- ``cardinality`` — ``SINGLE`` (a given object can have at most one tag from
  this category) or ``MULTIPLE``.
- ``associable_types`` — the inventory object types tags in this category may
  be applied to (``VirtualMachine``, ``HostSystem``, ``ClusterComputeResource``,
  etc.). An empty list means "any object type."

Tags can't exist without a category, so this is a prerequisite client for the
full tag lifecycle.
"""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/cis/tagging/category"


def list_(opts, profile=None):
    """List all category IDs."""
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, category_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{category_id}", profile=profile)


def get_or_none(opts, category_id, profile=None):
    try:
        return get(opts, category_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(
    opts,
    name,
    cardinality="SINGLE",
    description="",
    associable_types=None,
    profile=None,
):
    """Create a tag category. Returns the new category id."""
    body = {
        "name": name,
        "description": description,
        "cardinality": cardinality,
        "associable_types": list(associable_types or []),
    }
    return vcenter.api_post(opts, PATH, body=body, profile=profile)


def update(opts, category_id, spec, profile=None):
    """PATCH a tag category. *spec* keys: ``name``, ``description``,
    ``cardinality``, ``associable_types``.
    """
    return vcenter.api_patch(opts, f"{PATH}/{category_id}", body=dict(spec), profile=profile)


def delete(opts, category_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{category_id}", profile=profile)
