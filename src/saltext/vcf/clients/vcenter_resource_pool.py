"""vCenter resource pool."""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/resource-pool"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, rp_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{rp_id}", profile=profile)


def get_or_none(opts, rp_id, profile=None):
    try:
        return get(opts, rp_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, name, parent, **spec):
    """Create a resource pool under *parent* resource pool id."""
    body = {"name": name, "parent": parent}
    body.update(spec)
    return vcenter.api_post(opts, PATH, body=body)


def delete(opts, rp_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{rp_id}", profile=profile)


def tree(opts, profile=None):
    """Return ``{root_rp_id: {pool: {name, children: [...]}}}``.

    REST ``list_()`` returns only ``{resource_pool, name}``, so this walks
    each pool's detail (``get()``) to find its parent and composes the tree
    in Python. Pools whose parent is not in the result (cluster-root pools)
    become top-level keys.
    """
    pools = list_(opts, profile=profile)
    nodes = {}
    for p in pools:
        rp_id = p["resource_pool"]
        detail = get(opts, rp_id, profile=profile)
        nodes[rp_id] = {
            "resource_pool": rp_id,
            "name": p.get("name") or detail.get("name"),
            "parent": detail.get("parent"),
            "children": [],
        }
    roots = {}
    for rp_id, node in nodes.items():
        parent = node.get("parent")
        if parent and parent in nodes:
            nodes[parent]["children"].append(node)
        else:
            roots[rp_id] = node
    return roots
