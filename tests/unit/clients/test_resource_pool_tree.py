"""Tests for vcenter_resource_pool tree composition."""

import responses

from saltext.vcf.clients import vcenter_resource_pool


def test_tree_single_root_with_children(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/resource-pool",
        json=[
            {"resource_pool": "rp-1", "name": "Resources"},
            {"resource_pool": "rp-2", "name": "Child-A"},
            {"resource_pool": "rp-3", "name": "Grandchild"},
        ],
        status=200,
    )
    # detail calls — one per rp, in the order list returns them
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/resource-pool/rp-1",
        json={"name": "Resources", "parent": None},
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/resource-pool/rp-2",
        json={"name": "Child-A", "parent": "rp-1"},
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/resource-pool/rp-3",
        json={"name": "Grandchild", "parent": "rp-2"},
        status=200,
    )
    tree = vcenter_resource_pool.tree(opts)
    assert "rp-1" in tree
    children_of_root = tree["rp-1"]["children"]
    assert len(children_of_root) == 1
    assert children_of_root[0]["resource_pool"] == "rp-2"
    grandchildren = children_of_root[0]["children"]
    assert grandchildren[0]["resource_pool"] == "rp-3"


def test_tree_empty(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, "https://vc.test/api/vcenter/resource-pool", json=[], status=200
    )
    assert vcenter_resource_pool.tree(opts) == {}
