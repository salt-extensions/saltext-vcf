"""Tests for saltext.vmware.utils.vcenter."""

import pytest
import responses

from saltext.vmware.utils import vcenter


def test_get_config_default(opts):
    cfg = vcenter.get_config(opts)
    assert cfg == {
        "host": "vc.test",
        "username": "u",
        "password": "p",
        "verify_ssl": False,
    }


def test_get_config_profile(opts):
    cfg = vcenter.get_config(opts, profile="alt")
    assert cfg["host"] == "vc.alt"
    assert cfg["username"] == "u2"


def test_get_config_aliases(opts):
    opts["pillar"]["saltext.vmware"]["vcenter"] = {
        "hostname": "alias.test",
        "user": "alice",
        "password": "x",
    }
    cfg = vcenter.get_config(opts)
    assert cfg["host"] == "alias.test"
    assert cfg["username"] == "alice"
    assert cfg["verify_ssl"] is True  # default when omitted


def test_session_authenticates_once(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://vc.test/api/session",
        json="token-1",
        status=200,
    )
    mocked_responses.add(responses.GET, "https://vc.test/api/vcenter/cluster", json=[], status=200)
    mocked_responses.add(responses.GET, "https://vc.test/api/vcenter/host", json=[], status=200)

    vcenter.api_get(opts, "/api/vcenter/cluster")
    vcenter.api_get(opts, "/api/vcenter/host")

    auth_calls = [c for c in mocked_responses.calls if "api/session" in c.request.url]
    assert len(auth_calls) == 1


def test_invalidate_session(opts, mocked_responses):
    mocked_responses.add(responses.POST, "https://vc.test/api/session", json="t1", status=200)
    mocked_responses.add(responses.GET, "https://vc.test/api/vcenter/cluster", json=[], status=200)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", json="t2", status=200)
    mocked_responses.add(responses.GET, "https://vc.test/api/vcenter/cluster", json=[], status=200)

    vcenter.api_get(opts, "/api/vcenter/cluster")
    vcenter.invalidate_session(opts)
    vcenter.api_get(opts, "/api/vcenter/cluster")

    auth_calls = [c for c in mocked_responses.calls if "api/session" in c.request.url]
    assert len(auth_calls) == 2


def test_api_post_sends_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/cluster",
        json={"value": "cluster-1"},
        status=200,
    )
    result = vcenter.api_post(opts, "/api/vcenter/cluster", body={"name": "c1"})
    assert result == {"value": "cluster-1"}


def test_api_delete_returns_empty(opts, vcenter_authed):
    vcenter_authed.add(
        responses.DELETE,
        "https://vc.test/api/vcenter/cluster/c1",
        status=204,
    )
    assert vcenter.api_delete(opts, "/api/vcenter/cluster/c1") == {}


def test_api_patch(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PATCH,
        "https://vc.test/api/vcenter/cluster/c1",
        json={"value": "patched"},
        status=200,
    )
    assert vcenter.api_patch(opts, "/api/vcenter/cluster/c1", body={"x": 1}) == {"value": "patched"}


def test_http_error_propagates(opts, vcenter_authed):
    import requests

    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/cluster/missing", status=404)
    with pytest.raises(requests.HTTPError):
        vcenter.api_get(opts, "/api/vcenter/cluster/missing")
