"""Tests for the vcfa_organization client."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import vcfa_organization

_BASE = "https://vcfa.test/csp/gateway/am/api/orgs"


# -- list_ ---------------------------------------------------------------


def test_list_prefers_items_key(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        _BASE,
        json={"items": [{"id": "org-1", "displayName": "Org 1"}]},
        status=200,
    )
    assert vcfa_organization.list_(opts) == [{"id": "org-1", "displayName": "Org 1"}]


def test_list_falls_back_to_content_key(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        _BASE,
        json={"content": [{"id": "org-2"}]},
        status=200,
    )
    assert vcfa_organization.list_(opts) == [{"id": "org-2"}]


def test_list_empty(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, _BASE, json={}, status=200)
    assert vcfa_organization.list_(opts) == []


# -- get / get_or_none ---------------------------------------------------


def test_get_returns_body(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/org-1",
        json={"id": "org-1", "displayName": "Org 1"},
        status=200,
    )
    assert vcfa_organization.get(opts, "org-1") == {"id": "org-1", "displayName": "Org 1"}


def test_get_or_none_returns_none_on_404(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, f"{_BASE}/missing", json={"error": "not found"}, status=404)
    assert vcfa_organization.get_or_none(opts, "missing") is None


def test_get_or_none_reraises_non_404(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, f"{_BASE}/boom", json={"error": "boom"}, status=500)
    with pytest.raises(requests.HTTPError):
        vcfa_organization.get_or_none(opts, "boom")


# -- create --------------------------------------------------------------


def test_create_posts_spec_body(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, _BASE, json={"id": "org-9"}, status=200)
    spec = {"displayName": "Acme", "description": "acme tenant"}
    result = vcfa_organization.create(opts, spec)
    assert result == {"id": "org-9"}
    call = vcfa_authed.calls[-1]
    assert call.request.method == "POST"
    assert call.request.url == _BASE
    assert json.loads(call.request.body) == spec


# -- update --------------------------------------------------------------


def test_update_uses_patch(opts, vcfa_authed):
    vcfa_authed.add(responses.PATCH, f"{_BASE}/org-1", json={"id": "org-1"}, status=200)
    vcfa_organization.update(opts, "org-1", {"description": "renamed"})
    call = vcfa_authed.calls[-1]
    assert call.request.method == "PATCH"
    assert call.request.url == f"{_BASE}/org-1"
    assert json.loads(call.request.body) == {"description": "renamed"}


# -- delete --------------------------------------------------------------


def test_delete_hits_org_url(opts, vcfa_authed):
    vcfa_authed.add(responses.DELETE, f"{_BASE}/org-1", status=204)
    assert vcfa_organization.delete(opts, "org-1") == {}
    call = vcfa_authed.calls[-1]
    assert call.request.method == "DELETE"
    assert call.request.url == f"{_BASE}/org-1"


# -- list_services / enable_service / disable_service --------------------


def test_list_services_returns_items(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/org-1/service-definitions",
        json={"items": [{"id": "svc-1", "name": "iaas"}]},
        status=200,
    )
    assert vcfa_organization.list_services(opts, "org-1") == [{"id": "svc-1", "name": "iaas"}]


def test_list_services_falls_back_to_content(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/org-1/service-definitions",
        json={"content": [{"id": "svc-2"}]},
        status=200,
    )
    assert vcfa_organization.list_services(opts, "org-1") == [{"id": "svc-2"}]


def test_enable_service_posts_definition_id(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/org-1/service-definitions",
        json={"id": "svc-1"},
        status=200,
    )
    vcfa_organization.enable_service(opts, "org-1", "svc-1")
    call = vcfa_authed.calls[-1]
    assert call.request.method == "POST"
    assert call.request.url == f"{_BASE}/org-1/service-definitions"
    assert json.loads(call.request.body) == {"serviceDefinitionId": "svc-1"}


def test_disable_service_deletes_specific_definition(opts, vcfa_authed):
    vcfa_authed.add(
        responses.DELETE,
        f"{_BASE}/org-1/service-definitions/svc-1",
        status=204,
    )
    assert vcfa_organization.disable_service(opts, "org-1", "svc-1") == {}
    call = vcfa_authed.calls[-1]
    assert call.request.method == "DELETE"
    assert call.request.url == f"{_BASE}/org-1/service-definitions/svc-1"
