"""Tests for the vCenter polish clients: folder, resource_pool, content_library."""

import responses

from saltext.vcf.clients import vcenter_content_library
from saltext.vcf.clients import vcenter_folder
from saltext.vcf.clients import vcenter_resource_pool


def test_folder_list(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/folder",
        json=[{"folder": "f-1", "name": "vm", "type": "VIRTUAL_MACHINE"}],
        status=200,
    )
    assert vcenter_folder.list_(opts)[0]["folder"] == "f-1"


def test_folder_list_by_type(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/folder",
        json=[],
        status=200,
    )
    vcenter_folder.list_by_type(opts, "DATACENTER")
    assert "type=DATACENTER" in vcenter_authed.calls[-1].request.url


def test_folder_get_or_none(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/folder/missing", status=404)
    assert vcenter_folder.get_or_none(opts, "missing") is None


def test_resource_pool_list_and_create(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/resource-pool",
        json=[{"resource_pool": "rp-1", "name": "Resources"}],
        status=200,
    )
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/resource-pool",
        json="rp-99",
        status=200,
    )
    assert vcenter_resource_pool.list_(opts)[0]["resource_pool"] == "rp-1"
    assert vcenter_resource_pool.create(opts, "child", "rp-1") == "rp-99"


def test_content_library_list_local_subscribed(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/content/library", json=[], status=200)
    vcenter_authed.add(
        responses.GET, "https://vc.test/api/content/local-library", json=[], status=200
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/content/subscribed-library",
        json=[],
        status=200,
    )
    assert vcenter_content_library.list_(opts) == []
    assert vcenter_content_library.list_local(opts) == []
    assert vcenter_content_library.list_subscribed(opts) == []


def test_content_library_list_items_uses_query_param(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/content/library/item",
        json=[],
        status=200,
    )
    vcenter_content_library.list_items(opts, "lib-1")
    assert "library_id=lib-1" in vcenter_authed.calls[-1].request.url


def test_content_library_create_local_wraps_body(opts, vcenter_authed):
    import json

    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/content/local-library",
        json="lib-99",
        status=200,
    )
    assert (
        vcenter_content_library.create_local(
            opts, "MyLib", [{"type": "DATASTORE", "datastore_id": "ds-1"}]
        )
        == "lib-99"
    )
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["name"] == "MyLib"
    assert body["type"] == "LOCAL"
