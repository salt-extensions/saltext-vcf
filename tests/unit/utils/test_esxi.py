"""Tests for saltext.vmware.utils.esxi (direct/standalone mode)."""

import pytest
import responses

from saltext.vmware.utils import esxi


def test_get_config_default(opts):
    cfg = esxi.get_config(opts)
    assert cfg == {
        "host": "esxi.test",
        "username": "root",
        "password": "p",
        "verify_ssl": False,
    }


def test_session_authenticates_once(opts, mocked_responses):
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", json="tok", status=200)
    mocked_responses.add(responses.GET, "https://esxi.test/api/esx/host", json={}, status=200)
    mocked_responses.add(responses.GET, "https://esxi.test/api/esx/services", json=[], status=200)
    esxi.api_get(opts, "/api/esx/host")
    esxi.api_get(opts, "/api/esx/services")
    auth_calls = [c for c in mocked_responses.calls if "api/session" in c.request.url]
    assert len(auth_calls) == 1


def test_api_patch(opts, esxi_authed):
    esxi_authed.add(
        responses.PATCH,
        "https://esxi.test/api/esx/ntp",
        json={"servers": ["pool.ntp.org"]},
        status=200,
    )
    assert esxi.api_patch(opts, "/api/esx/ntp", body={"servers": ["pool.ntp.org"]}) == {
        "servers": ["pool.ntp.org"]
    }


def test_invalidate_session(opts, mocked_responses):
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", json="t1", status=200)
    mocked_responses.add(responses.GET, "https://esxi.test/api/esx/host", json={}, status=200)
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", json="t2", status=200)
    mocked_responses.add(responses.GET, "https://esxi.test/api/esx/host", json={}, status=200)
    esxi.api_get(opts, "/api/esx/host")
    esxi.invalidate_session(opts)
    esxi.api_get(opts, "/api/esx/host")
    auth_calls = [c for c in mocked_responses.calls if "api/session" in c.request.url]
    assert len(auth_calls) == 2


def test_http_error_propagates(opts, esxi_authed):
    import requests

    esxi_authed.add(responses.GET, "https://esxi.test/api/esx/host", status=500)
    with pytest.raises(requests.HTTPError):
        esxi.api_get(opts, "/api/esx/host")
