"""Tests for vcfa_policy and vcfa_catalog."""

import json

import responses

from saltext.vcf.clients import vcfa_catalog
from saltext.vcf.clients import vcfa_policy

# -- policy --------------------------------------------------------------


def test_policy_list_filters_by_project(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/policy/api/policies",
        json={"content": []},
        status=200,
    )
    vcfa_policy.list_(opts, project_id="p-1")
    assert "projectId=p-1" in vcfa_authed.calls[-1].request.url


def test_policy_create_passes_through(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/policy/api/policies",
        json={"id": "pol-1"},
        status=200,
    )
    spec = {
        "name": "approval",
        "typeId": "com.vmware.policy.approval",
        "projectId": "p-1",
        "definition": {"approvers": ["admin@x"]},
    }
    vcfa_policy.create(opts, spec)
    assert json.loads(vcfa_authed.calls[-1].request.body) == spec


def test_policy_list_types(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/policy/api/types",
        json={"content": [{"id": "com.vmware.policy.approval"}]},
        status=200,
    )
    out = vcfa_policy.list_types(opts)
    assert out == [{"id": "com.vmware.policy.approval"}]


# -- catalog -------------------------------------------------------------


def test_catalog_list_items(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/catalog/api/items",
        json={"content": [{"id": "ci-1"}]},
        status=200,
    )
    assert vcfa_catalog.list_items(opts) == [{"id": "ci-1"}]


def test_catalog_request_item(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/catalog/api/items/ci-1/request",
        json={"deploymentId": "dep-1"},
        status=200,
    )
    out = vcfa_catalog.request_item(opts, "ci-1", {"projectId": "p-1"})
    assert out == {"deploymentId": "dep-1"}


def test_catalog_create_source(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/catalog/api/sources",
        json={"id": "src-1"},
        status=200,
    )
    vcfa_catalog.create_source(opts, {"name": "src", "typeId": "com.vmw.blueprint"})


def test_catalog_update_source_is_patch(opts, vcfa_authed):
    vcfa_authed.add(
        responses.PATCH,
        "https://vcfa.test/catalog/api/sources/src-1",
        json={"id": "src-1"},
        status=200,
    )
    vcfa_catalog.update_source(opts, "src-1", {"name": "renamed"})
