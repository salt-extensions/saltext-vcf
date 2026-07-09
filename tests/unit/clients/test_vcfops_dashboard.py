"""Tests for clients.vcfops_dashboard."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import vcfops_dashboard as d

_BASE = "https://ops.test/suite-api/api/dashboards"


def test_list_returns_api_body(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        _BASE,
        json={"dashboards": [{"id": "d1"}, {"id": "d2"}]},
        status=200,
    )
    out = d.list_(opts)
    assert out == {"dashboards": [{"id": "d1"}, {"id": "d2"}]}


def test_get_returns_dashboard(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/d1",
        json={"id": "d1", "name": "capacity"},
        status=200,
    )
    assert d.get(opts, "d1") == {"id": "d1", "name": "capacity"}


def test_get_raises_http_error(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/missing",
        json={"error": "not found"},
        status=404,
    )
    with pytest.raises(requests.HTTPError):
        d.get(opts, "missing")


def test_get_or_none_returns_none_on_404(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/missing",
        json={"error": "not found"},
        status=404,
    )
    assert d.get_or_none(opts, "missing") is None


def test_get_or_none_propagates_other_http_errors(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/boom",
        json={"error": "server exploded"},
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        d.get_or_none(opts, "boom")


def test_get_or_none_returns_body_when_present(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/d1",
        json={"id": "d1"},
        status=200,
    )
    assert d.get_or_none(opts, "d1") == {"id": "d1"}


def test_create_posts_spec(opts, vcfops_authed):
    spec = {"name": "capacity", "widgets": []}
    vcfops_authed.add(
        responses.POST,
        _BASE,
        json={"id": "d1", "name": "capacity"},
        status=201,
    )
    out = d.create(opts, spec)
    assert out == {"id": "d1", "name": "capacity"}
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body == spec


def test_create_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        _BASE,
        json={"error": "bad spec"},
        status=400,
    )
    with pytest.raises(requests.HTTPError):
        d.create(opts, {"name": "x"})


def test_update_puts_spec(opts, vcfops_authed):
    spec = {"name": "capacity-v2"}
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/d1",
        json={"id": "d1", "name": "capacity-v2"},
        status=200,
    )
    out = d.update(opts, "d1", spec)
    assert out == {"id": "d1", "name": "capacity-v2"}
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body == spec


def test_update_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/missing",
        json={"error": "gone"},
        status=404,
    )
    with pytest.raises(requests.HTTPError):
        d.update(opts, "missing", {"name": "x"})


def test_delete_sends_delete(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_BASE}/d1", status=204)
    assert d.delete(opts, "d1") == {}
    assert vcfops_authed.calls[-1].request.method == "DELETE"


def test_delete_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_BASE}/missing", status=404)
    with pytest.raises(requests.HTTPError):
        d.delete(opts, "missing")


def test_share_posts_to_share_path(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/d1/share/user-42",
        json={"status": "shared"},
        status=200,
    )
    out = d.share(opts, "d1", "user-42")
    assert out == {"status": "shared"}
    assert vcfops_authed.calls[-1].request.url.endswith("/dashboards/d1/share/user-42")


def test_share_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/d1/share/user-42",
        json={"error": "no such user"},
        status=404,
    )
    with pytest.raises(requests.HTTPError):
        d.share(opts, "d1", "user-42")


def test_import_posts_to_import_endpoint(opts, vcfops_authed):
    payload = {"name": "imported", "widgets": [{"kind": "gauge"}]}
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/import",
        json={"id": "d99", "name": "imported"},
        status=201,
    )
    out = d.import_(opts, payload)
    assert out == {"id": "d99", "name": "imported"}
    req = vcfops_authed.calls[-1].request
    assert req.url.endswith("/dashboards/import")
    assert json.loads(req.body) == payload


def test_import_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/import",
        json={"error": "invalid payload"},
        status=400,
    )
    with pytest.raises(requests.HTTPError):
        d.import_(opts, {"broken": True})


def test_profile_is_forwarded_to_utils_layer(opts, vcfops_authed, monkeypatch):
    """Confirm the ``profile`` kwarg reaches the util layer."""
    seen = {}

    real_api_get = d.vcfops.api_get

    def spy(opts_, path, params=None, profile=None):
        seen["profile"] = profile
        return real_api_get(opts_, path, params=params, profile=profile)

    monkeypatch.setattr(d.vcfops, "api_get", spy)
    vcfops_authed.add(responses.GET, _BASE, json={"dashboards": []}, status=200)
    d.list_(opts, profile="alt")
    assert seen["profile"] == "alt"
