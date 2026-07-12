"""Tests for the vCenter SSO identity client."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import vcenter_sso

_BASE = "https://vc.test/api/vcenter/identity"


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


def test_providers_list(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/providers",
        json=[{"provider": "p-1", "config_tag": "ActiveDirectory"}],
        status=200,
    )
    result = vcenter_sso.providers_list(opts)
    assert result[0]["provider"] == "p-1"


def test_providers_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/providers/p-1",
        json={"provider": "p-1", "config_tag": "ActiveDirectory"},
        status=200,
    )
    assert vcenter_sso.providers_get(opts, "p-1")["provider"] == "p-1"


def test_providers_get_or_none_missing(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/providers/nope", status=404)
    assert vcenter_sso.providers_get_or_none(opts, "nope") is None


def test_providers_get_or_none_propagates_500(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/providers/boom", status=500)
    with pytest.raises(requests.HTTPError):
        vcenter_sso.providers_get_or_none(opts, "boom")


def test_providers_create_posts_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{_BASE}/providers",
        json="p-99",
        status=200,
    )
    spec = {
        "config_tag": "ActiveDirectory",
        "domain_name": "corp.example",
        "username": "svc",
        "password": "s3cr3t",
    }
    assert vcenter_sso.providers_create(opts, spec) == "p-99"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == spec


def test_providers_update_patches_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PATCH,
        f"{_BASE}/providers/p-1",
        json={},
        status=200,
    )
    vcenter_sso.providers_update(opts, "p-1", {"username": "svc2"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"username": "svc2"}


def test_providers_delete(opts, vcenter_authed):
    vcenter_authed.add(responses.DELETE, f"{_BASE}/providers/p-1", json={}, status=200)
    vcenter_sso.providers_delete(opts, "p-1")
    assert vcenter_authed.calls[-1].request.method == "DELETE"
    assert vcenter_authed.calls[-1].request.url.endswith("/providers/p-1")


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


def test_groups_list_no_domain(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/groups", json=[], status=200)
    vcenter_sso.groups_list(opts)
    assert "domain=" not in vcenter_authed.calls[-1].request.url


def test_groups_list_with_domain(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/groups", json=[], status=200)
    vcenter_sso.groups_list(opts, domain="vsphere.local")
    assert "domain=vsphere.local" in vcenter_authed.calls[-1].request.url


def test_groups_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/groups/g-1",
        json={"group": "g-1", "name": "Administrators"},
        status=200,
    )
    assert vcenter_sso.groups_get(opts, "g-1")["name"] == "Administrators"


def test_groups_get_or_none_missing(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/groups/nope", status=404)
    assert vcenter_sso.groups_get_or_none(opts, "nope") is None


def test_groups_get_or_none_propagates(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/groups/boom", status=503)
    with pytest.raises(requests.HTTPError):
        vcenter_sso.groups_get_or_none(opts, "boom")


def test_groups_create_posts_body(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{_BASE}/groups", json="g-99", status=200)
    assert vcenter_sso.groups_create(opts, "Ops", "vsphere.local", description="ops team") == "g-99"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"name": "Ops", "domain": "vsphere.local", "description": "ops team"}


def test_groups_update_patches_body(opts, vcenter_authed):
    vcenter_authed.add(responses.PATCH, f"{_BASE}/groups/g-1", json={}, status=200)
    vcenter_sso.groups_update(opts, "g-1", {"description": "renamed"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"description": "renamed"}


def test_groups_delete(opts, vcenter_authed):
    vcenter_authed.add(responses.DELETE, f"{_BASE}/groups/g-1", json={}, status=200)
    vcenter_sso.groups_delete(opts, "g-1")
    assert vcenter_authed.calls[-1].request.method == "DELETE"


def test_group_add_member(opts, vcenter_authed):
    vcenter_authed.add(responses.PATCH, f"{_BASE}/groups/g-1/members", json={}, status=200)
    vcenter_sso.group_add_member(opts, "g-1", "alice@vsphere.local")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"members_to_add": ["alice@vsphere.local"]}


def test_group_remove_member(opts, vcenter_authed):
    vcenter_authed.add(responses.PATCH, f"{_BASE}/groups/g-1/members", json={}, status=200)
    vcenter_sso.group_remove_member(opts, "g-1", "alice@vsphere.local")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"members_to_remove": ["alice@vsphere.local"]}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def test_users_list_no_domain(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/users", json=[], status=200)
    vcenter_sso.users_list(opts)
    assert "domain=" not in vcenter_authed.calls[-1].request.url


def test_users_list_with_domain(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/users", json=[], status=200)
    vcenter_sso.users_list(opts, domain="vsphere.local")
    assert "domain=vsphere.local" in vcenter_authed.calls[-1].request.url


def test_users_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/users/alice",
        json={"user": "alice", "domain": "vsphere.local"},
        status=200,
    )
    assert vcenter_sso.users_get(opts, "alice")["user"] == "alice"


def test_users_get_or_none_missing(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/users/nope", status=404)
    assert vcenter_sso.users_get_or_none(opts, "nope") is None


def test_users_get_or_none_propagates(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/users/boom", status=500)
    with pytest.raises(requests.HTTPError):
        vcenter_sso.users_get_or_none(opts, "boom")


def test_users_create_minimal(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{_BASE}/users", json="u-99", status=200)
    assert vcenter_sso.users_create(opts, "alice", "vsphere.local", "hunter2") == "u-99"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {
        "username": "alice",
        "domain": "vsphere.local",
        "password": "hunter2",
        "description": "",
    }
    # No email field by default.
    assert "email" not in body


def test_users_create_with_email(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{_BASE}/users", json="u-100", status=200)
    vcenter_sso.users_create(
        opts,
        "bob",
        "vsphere.local",
        "hunter2",
        description="ops",
        email="bob@example.com",
    )
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["email"] == "bob@example.com"
    assert body["description"] == "ops"


def test_users_update_patches_body(opts, vcenter_authed):
    vcenter_authed.add(responses.PATCH, f"{_BASE}/users/alice", json={}, status=200)
    vcenter_sso.users_update(opts, "alice", {"description": "renamed"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"description": "renamed"}


def test_users_delete(opts, vcenter_authed):
    vcenter_authed.add(responses.DELETE, f"{_BASE}/users/alice", json={}, status=200)
    vcenter_sso.users_delete(opts, "alice")
    assert vcenter_authed.calls[-1].request.method == "DELETE"
    assert vcenter_authed.calls[-1].request.url.endswith("/users/alice")
