"""Tests for vcfa_cloud_template (blueprint API)."""

import json

import responses

from saltext.vcf.clients import vcfa_cloud_template as t

_BASE = "https://vcfa.test/blueprint/api/blueprints"


def test_list_unwraps_content(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, _BASE, json={"content": [{"id": "bp-1"}]}, status=200)
    assert t.list_(opts) == [{"id": "bp-1"}]


def test_list_filters_by_project(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, _BASE, json={"content": []}, status=200)
    t.list_(opts, project_id="proj-1")
    assert "projects=proj-1" in vcfa_authed.calls[-1].request.url


def test_create_sends_body(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, _BASE, json={"id": "bp-1"}, status=200)
    t.create(opts, {"name": "bp", "projectId": "p", "content": "..."})
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body["name"] == "bp"


def test_update_is_put(opts, vcfa_authed):
    vcfa_authed.add(responses.PUT, f"{_BASE}/bp-1", json={"id": "bp-1"}, status=200)
    t.update(opts, "bp-1", {"name": "bp-new"})


def test_versions_lifecycle(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET, f"{_BASE}/bp-1/versions", json={"content": [{"id": "v-1"}]}, status=200
    )
    assert t.list_versions(opts, "bp-1") == [{"id": "v-1"}]

    vcfa_authed.add(responses.POST, f"{_BASE}/bp-1/versions", json={"id": "v-2"}, status=200)
    t.create_version(opts, "bp-1", {"version": "1.0", "release": True})

    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/bp-1/versions/v-1/actions/release",
        json={},
        status=200,
    )
    t.release_version(opts, "bp-1", "v-1")

    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/bp-1/versions/v-1/actions/unrelease",
        json={},
        status=200,
    )
    t.unrelease_version(opts, "bp-1", "v-1")
