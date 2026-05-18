"""Tests for the vCenter tag-category client + updated tag client.

vCenter 9 dropped the legacy ``{"create_spec": {...}}`` wrapper on the
tagging API. These tests pin the new flat-spec wire format.
"""

import json

import responses

from saltext.vcf.clients import vcenter_tag
from saltext.vcf.clients import vcenter_tag_category as c

BASE = "https://vc.test"
CATEGORY = f"{BASE}/api/cis/tagging/category"
TAG = f"{BASE}/api/cis/tagging/tag"


def test_category_list(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, CATEGORY, json=["cat-1", "cat-2"], status=200)
    assert c.list_(opts) == ["cat-1", "cat-2"]


def test_category_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, f"{CATEGORY}/cat-1", json={"id": "cat-1", "name": "owner"}, status=200
    )
    assert c.get(opts, "cat-1")["name"] == "owner"


def test_category_get_or_none_404(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{CATEGORY}/missing", status=404)
    assert c.get_or_none(opts, "missing") is None


def test_category_create_flat_spec(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, CATEGORY, json="cat-99", status=200)
    out = c.create(opts, "owner", cardinality="MULTIPLE", associable_types=["VirtualMachine"])
    assert out == "cat-99"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {
        "name": "owner",
        "description": "",
        "cardinality": "MULTIPLE",
        "associable_types": ["VirtualMachine"],
    }


def test_category_update(opts, vcenter_authed):
    vcenter_authed.add(responses.PATCH, f"{CATEGORY}/cat-1", json={}, status=200)
    c.update(opts, "cat-1", {"description": "new"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"description": "new"}


def test_category_delete(opts, vcenter_authed):
    vcenter_authed.add(responses.DELETE, f"{CATEGORY}/cat-1", json=None, status=200)
    c.delete(opts, "cat-1")


# Tag client: flat-spec format (was wrapped before)


def test_tag_create_flat_spec(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, TAG, json="tag-99", status=200)
    vcenter_tag.create(opts, "prod", "cat-1", description="env=prod")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"name": "prod", "category_id": "cat-1", "description": "env=prod"}


def test_tag_update(opts, vcenter_authed):
    vcenter_authed.add(responses.PATCH, f"{TAG}/tag-1", json={}, status=200)
    vcenter_tag.update(opts, "tag-1", {"name": "renamed"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"name": "renamed"}


def test_module_wrappers_delegate(opts, monkeypatch, vcenter_authed):
    from saltext.vcf.modules import vcf_vcenter_tag
    from saltext.vcf.modules import vcf_vcenter_tag_category

    monkeypatch.setattr(vcf_vcenter_tag, "__opts__", opts, raising=False)
    monkeypatch.setattr(vcf_vcenter_tag_category, "__opts__", opts, raising=False)

    vcenter_authed.add(responses.POST, CATEGORY, json="cat-z", status=200)
    vcenter_authed.add(responses.POST, TAG, json="tag-z", status=200)
    vcenter_authed.add(responses.PATCH, f"{TAG}/tag-z", json={}, status=200)

    assert vcf_vcenter_tag_category.create("owner") == "cat-z"
    assert vcf_vcenter_tag.create("prod", "cat-z") == "tag-z"
    vcf_vcenter_tag.update("tag-z", {"description": "x"})
