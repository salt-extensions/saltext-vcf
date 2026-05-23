"""Tests for vcfa_project and vcfa_project_user."""

import json

import pytest
import responses

from saltext.vcf.clients import vcfa_project
from saltext.vcf.clients import vcfa_project_user

_BASE = "https://vcfa.test/iaas/api/projects"


def test_project_list(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, _BASE, json={"content": [{"id": "p-1"}]}, status=200)
    assert vcfa_project.list_(opts) == [{"id": "p-1"}]


def test_project_create_sends_body(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, _BASE, json={"id": "p-1"}, status=200)
    vcfa_project.create(opts, {"name": "p"})
    assert json.loads(vcfa_authed.calls[-1].request.body) == {"name": "p"}


def test_project_update_is_patch(opts, vcfa_authed):
    vcfa_authed.add(responses.PATCH, f"{_BASE}/p-1", json={"id": "p-1"}, status=200)
    vcfa_project.update(opts, "p-1", {"description": "x"})


def test_project_resources(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, f"{_BASE}/p-1/resources", json={"content": []}, status=200)
    assert vcfa_project.resources(opts, "p-1") == {"content": []}


# -- project_user ----------------------------------------------------------


def test_list_members_all_roles(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/p-1",
        json={
            "id": "p-1",
            "administrators": [{"email": "a@x"}],
            "members": [{"email": "b@x"}],
            "viewers": [],
            "supervisors": [],
        },
        status=200,
    )
    out = vcfa_project_user.list_members(opts, "p-1")
    assert out["administrators"] == [{"email": "a@x"}]
    assert out["members"] == [{"email": "b@x"}]
    assert out["viewers"] == []
    assert out["supervisors"] == []


def test_list_members_single_role(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/p-1",
        json={
            "administrators": [{"email": "a@x"}],
            "members": [],
            "viewers": [],
            "supervisors": [],
        },
        status=200,
    )
    assert vcfa_project_user.list_members(opts, "p-1", role="administrators") == [{"email": "a@x"}]


def test_list_members_unknown_role_raises(opts):
    with pytest.raises(ValueError):
        vcfa_project_user.list_members(opts, "p-1", role="bogus")


def test_add_member_skips_when_present(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/p-1",
        json={
            "administrators": [],
            "members": [{"email": "a@x", "type": "user"}],
            "viewers": [],
            "supervisors": [],
        },
        status=200,
    )
    vcfa_project_user.add_member(opts, "p-1", "members", "a@x")
    # No PATCH should have been issued.
    methods = [c.request.method for c in vcfa_authed.calls]
    assert "PATCH" not in methods


def test_add_member_patches_when_missing(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/p-1",
        json={"administrators": [], "members": [], "viewers": [], "supervisors": []},
        status=200,
    )
    vcfa_authed.add(responses.PATCH, f"{_BASE}/p-1", json={"id": "p-1"}, status=200)
    vcfa_project_user.add_member(opts, "p-1", "members", "a@x")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"members": [{"email": "a@x", "type": "user"}]}


def test_remove_member_filters_role_array(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/p-1",
        json={
            "administrators": [],
            "members": [{"email": "a@x", "type": "user"}, {"email": "b@x", "type": "user"}],
            "viewers": [],
            "supervisors": [],
        },
        status=200,
    )
    vcfa_authed.add(responses.PATCH, f"{_BASE}/p-1", json={"id": "p-1"}, status=200)
    vcfa_project_user.remove_member(opts, "p-1", "members", "a@x")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"members": [{"email": "b@x", "type": "user"}]}


def test_set_members_replaces_wholesale(opts, vcfa_authed):
    vcfa_authed.add(responses.PATCH, f"{_BASE}/p-1", json={"id": "p-1"}, status=200)
    vcfa_project_user.set_members(opts, "p-1", "members", ["a@x", "b@x"])
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"members": [{"email": "a@x", "type": "user"}, {"email": "b@x", "type": "user"}]}
