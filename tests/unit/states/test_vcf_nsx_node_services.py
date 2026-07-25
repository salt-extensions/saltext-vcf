"""Tests for states.vcf_nsx_node_services."""

import pytest

from saltext.vcf.clients import nsx_node_services as c
from saltext.vcf.states import vcf_nsx_node_services as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "current": {
            "service_name": "http",
            "service_properties": {
                "client_api_rate_limit": 40,
                "client_api_concurrency_limit": 20,
                "global_api_concurrency_limit": 199,
                "connection_timeout": 30,
                "redirect_host": "keep-me.example.test",
            },
        },
        "puts": [],
    }

    def _get(opts, profile=None):
        return state["current"]

    def _put(opts, body, profile=None):
        state["puts"].append(body)
        state["current"] = body
        return body

    monkeypatch.setattr(c, "http_get", _get)
    monkeypatch.setattr(c, "http_put", _put)
    return state


def test_http_configured_idempotent(stub):
    ret = st.http_configured(
        "nsx-http",
        client_api_rate_limit=40,
        client_api_concurrency_limit=20,
        global_api_concurrency_limit=199,
    )
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["puts"] == []


def test_http_configured_updates_diff(stub):
    ret = st.http_configured(
        "nsx-http",
        client_api_rate_limit=100,
        client_api_concurrency_limit=40,
        global_api_concurrency_limit=199,
    )
    assert ret["result"] is True
    assert set(ret["changes"]) == {"client_api_rate_limit", "client_api_concurrency_limit"}
    assert ret["changes"]["client_api_rate_limit"] == {"old": 40, "new": 100}
    assert len(stub["puts"]) == 1


def test_http_configured_merges_preserves_unrelated_fields(stub):
    """State must read + merge before PUTting since the endpoint is total-replace."""
    st.http_configured(
        "nsx-http",
        client_api_rate_limit=100,
    )
    sent = stub["puts"][0]
    props = sent["service_properties"]
    # Changed field
    assert props["client_api_rate_limit"] == 100
    # Everything else preserved
    assert props["client_api_concurrency_limit"] == 20
    assert props["global_api_concurrency_limit"] == 199
    assert props["connection_timeout"] == 30
    assert props["redirect_host"] == "keep-me.example.test"


def test_http_configured_test_mode(stub, monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.http_configured("nsx-http", client_api_rate_limit=100)
    assert ret["result"] is None
    assert ret["changes"] == {"client_api_rate_limit": {"old": 40, "new": 100}}
    assert stub["puts"] == []


def test_http_configured_no_fields_noop(stub):
    ret = st.http_configured("nsx-http")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["puts"] == []


def test_http_configured_passes_extra_fields(stub):
    ret = st.http_configured(
        "nsx-http",
        connection_timeout=45,
        redirect_host="new-host.example.test",
    )
    assert set(ret["changes"]) == {"connection_timeout", "redirect_host"}
    sent = stub["puts"][0]["service_properties"]
    assert sent["connection_timeout"] == 45
    assert sent["redirect_host"] == "new-host.example.test"
    # Rate-limit fields untouched
    assert sent["client_api_rate_limit"] == 40
