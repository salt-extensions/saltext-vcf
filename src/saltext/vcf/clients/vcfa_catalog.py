"""VCF Automation — catalog (``/catalog/api``).

The catalog surface has two halves:

* **items** — the published things end-users can request (each backed
  by a blueprint version, ABX action, vRO workflow, or other catalog
  source).
* **sources** — the source registrations that populate items. A
  source binds a backing type (blueprint, abx, vro) to a project and
  manages which versions are exposed.
"""

import requests

from saltext.vcf.utils import vcfa

_ITEMS = "/catalog/api/items"
_SOURCES = "/catalog/api/sources"


def list_items(opts, project_id=None, profile=None):
    params = {}
    if project_id is not None:
        params["projects"] = project_id
    resp = vcfa.api_get(opts, _ITEMS, params=params or None, profile=profile)
    return resp.get("content", []) or []


def get_item(opts, item_id, profile=None):
    return vcfa.api_get(opts, f"{_ITEMS}/{item_id}", profile=profile)


def get_item_or_none(opts, item_id, profile=None):
    try:
        return get_item(opts, item_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def request_item(opts, item_id, request_spec, profile=None):
    """Submit a catalog request and return the response.

    Most callers will want to follow the deployment with
    :func:`saltext.vcf.utils.vcfa.wait_for_deployment` using the
    returned ``deploymentId``.
    """
    return vcfa.api_post(opts, f"{_ITEMS}/{item_id}/request", body=request_spec, profile=profile)


def list_sources(opts, profile=None):
    resp = vcfa.api_get(opts, _SOURCES, profile=profile)
    return resp.get("content", []) or []


def get_source(opts, source_id, profile=None):
    return vcfa.api_get(opts, f"{_SOURCES}/{source_id}", profile=profile)


def create_source(opts, spec, profile=None):
    """Create a catalog source.

    *spec* keys: ``name``, ``description``, ``typeId`` (e.g.
    ``com.vmw.blueprint``, ``com.vmw.abx.actions``,
    ``com.vmw.vro.workflow``), ``projectId``, ``config`` (type-specific).
    """
    return vcfa.api_post(opts, _SOURCES, body=spec, profile=profile)


def update_source(opts, source_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_SOURCES}/{source_id}", body=spec, profile=profile)


def delete_source(opts, source_id, profile=None):
    return vcfa.api_delete(opts, f"{_SOURCES}/{source_id}", profile=profile)
