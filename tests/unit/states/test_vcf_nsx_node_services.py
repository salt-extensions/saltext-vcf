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


# ---------------------------------------------------------------------------
# tls_configured — ISA Encryption Requirements / STIG 912 TLS 1.2
# ---------------------------------------------------------------------------


@pytest.fixture
def tls_stub(monkeypatch):
    """Stub with an existing TLS + rate-limit config to prove field isolation."""
    state = {
        "current": {
            "service_name": "http",
            "service_properties": {
                # DoS-mitigation fields — must survive TLS-only updates
                "client_api_rate_limit": 40,
                "client_api_concurrency_limit": 20,
                "global_api_concurrency_limit": 199,
                "connection_timeout": 30,
                "redirect_host": "keep-me.example.test",
                # TLS fields
                "protocols": ["TLSv1_2"],
                "cipher_suites": ["TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"],
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


def test_tls_configured_idempotent(tls_stub):
    ret = st.tls_configured(
        "nsx-tls",
        protocols=["TLSv1_2"],
        cipher_suites=["TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"],
    )
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert tls_stub["puts"] == []


def test_tls_configured_updates_diff(tls_stub):
    ret = st.tls_configured(
        "nsx-tls",
        protocols=["TLSv1_2", "TLSv1_3"],
    )
    assert ret["result"] is True
    assert set(ret["changes"]) == {"protocols"}
    assert ret["changes"]["protocols"] == {
        "old": ["TLSv1_2"],
        "new": ["TLSv1_2", "TLSv1_3"],
    }
    assert len(tls_stub["puts"]) == 1


def test_tls_configured_preserves_rate_limit_fields(tls_stub):
    """Regression: total-replace endpoint must not clobber DoS-mitigation fields."""
    st.tls_configured(
        "nsx-tls",
        protocols=["TLSv1_2", "TLSv1_3"],
        cipher_suites=[
            "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
            "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
        ],
    )
    sent_props = tls_stub["puts"][0]["service_properties"]
    # TLS fields updated
    assert sent_props["protocols"] == ["TLSv1_2", "TLSv1_3"]
    assert sent_props["cipher_suites"] == [
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
    ]
    # Every unrelated field preserved verbatim
    assert sent_props["client_api_rate_limit"] == 40
    assert sent_props["client_api_concurrency_limit"] == 20
    assert sent_props["global_api_concurrency_limit"] == 199
    assert sent_props["connection_timeout"] == 30
    assert sent_props["redirect_host"] == "keep-me.example.test"


def test_tls_configured_partial_update_keeps_other_tls_field(tls_stub):
    """cipher_suites=None must not overwrite the current cipher_suites."""
    st.tls_configured(
        "nsx-tls",
        protocols=["TLSv1_2", "TLSv1_3"],
    )
    sent_props = tls_stub["puts"][0]["service_properties"]
    assert sent_props["protocols"] == ["TLSv1_2", "TLSv1_3"]
    # cipher_suites untouched
    assert sent_props["cipher_suites"] == ["TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"]


def test_tls_configured_test_mode(tls_stub, monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.tls_configured("nsx-tls", protocols=["TLSv1_2", "TLSv1_3"])
    assert ret["result"] is None
    assert ret["changes"] == {
        "protocols": {"old": ["TLSv1_2"], "new": ["TLSv1_2", "TLSv1_3"]}
    }
    assert tls_stub["puts"] == []


def test_tls_configured_no_fields_noop(tls_stub):
    ret = st.tls_configured("nsx-tls")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert tls_stub["puts"] == []


def test_http_configured_preserves_tls_fields(tls_stub):
    """Symmetric regression: HTTP rate-limit update must not clobber TLS fields."""
    st.http_configured("nsx-http", client_api_rate_limit=100)
    sent_props = tls_stub["puts"][0]["service_properties"]
    assert sent_props["client_api_rate_limit"] == 100
    assert sent_props["protocols"] == ["TLSv1_2"]
    assert sent_props["cipher_suites"] == ["TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"]


# ---------------------------------------------------------------------------
# client — http_set / http_tls_set keyword passthrough
# ---------------------------------------------------------------------------


def test_client_http_set_accepts_tls_fields(monkeypatch, opts):
    """http_set must pass cipher_suites / protocols through onto service_properties."""
    captured = {}

    def _get(opts, profile=None):
        return {
            "service_name": "http",
            "service_properties": {
                "client_api_rate_limit": 40,
                "protocols": ["TLSv1_2"],
            },
        }

    def _put(opts, body, profile=None):
        captured["body"] = body
        return body

    monkeypatch.setattr(c, "http_get", _get)
    monkeypatch.setattr(c, "http_put", _put)

    c.http_set(
        opts,
        cipher_suites=["TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"],
        protocols=["TLSv1_2", "TLSv1_3"],
    )
    props = captured["body"]["service_properties"]
    assert props["cipher_suites"] == ["TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"]
    assert props["protocols"] == ["TLSv1_2", "TLSv1_3"]
    # Untouched
    assert props["client_api_rate_limit"] == 40


def test_client_http_tls_set_only_touches_tls_fields(monkeypatch, opts):
    captured = {}

    def _get(opts, profile=None):
        return {
            "service_name": "http",
            "service_properties": {
                "client_api_rate_limit": 40,
                "redirect_host": "keep-me.example.test",
                "protocols": ["TLSv1_2"],
            },
        }

    def _put(opts, body, profile=None):
        captured["body"] = body
        return body

    monkeypatch.setattr(c, "http_get", _get)
    monkeypatch.setattr(c, "http_put", _put)

    c.http_tls_set(opts, protocols=["TLSv1_2", "TLSv1_3"])
    props = captured["body"]["service_properties"]
    assert props["protocols"] == ["TLSv1_2", "TLSv1_3"]
    # cipher_suites was None → not injected
    assert "cipher_suites" not in props
    # DoS-mitigation fields intact
    assert props["client_api_rate_limit"] == 40
    assert props["redirect_host"] == "keep-me.example.test"
