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
# logging_level_configured
# ---------------------------------------------------------------------------


@pytest.fixture
def logging_stub(monkeypatch):
    """Stub client.service_get / service_put with per-service state."""
    services = {
        "manager": {
            "service_name": "manager",
            "service_properties": {"logging_level": "INFO", "keep_me": "yes"},
        },
        "policy": {
            "service_name": "policy",
            "service_properties": {"logging_level": "INFO"},
        },
        "async_replicator": {
            "service_name": "async_replicator",
            "service_properties": {"logging_level": "INFO"},
        },
        "http": {
            "service_name": "http",
            "service_properties": {"logging_level": "INFO", "client_api_rate_limit": 100},
        },
    }
    puts = []

    def _get(opts, service_name, profile=None):
        return services[service_name]

    def _put(opts, service_name, body, profile=None):
        puts.append((service_name, body))
        services[service_name] = body
        return body

    monkeypatch.setattr(c, "service_get", _get)
    monkeypatch.setattr(c, "service_put", _put)
    return {"services": services, "puts": puts}


def test_logging_level_configured_idempotent(logging_stub):
    ret = st.logging_level_configured("audit-manager", service="manager", level="INFO")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert logging_stub["puts"] == []
    assert "already" in ret["comment"]


def test_logging_level_configured_case_insensitive(logging_stub):
    """INFO on the wire vs 'info' from pillar must still be a no-op."""
    ret = st.logging_level_configured("audit-manager", service="manager", level="info")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert logging_stub["puts"] == []


def test_logging_level_configured_updates(logging_stub):
    ret = st.logging_level_configured("audit-manager", service="manager", level="DEBUG")
    assert ret["result"] is True
    assert ret["changes"] == {"logging_level": {"old": "INFO", "new": "DEBUG"}}
    assert len(logging_stub["puts"]) == 1
    service_name, body = logging_stub["puts"][0]
    assert service_name == "manager"
    # Preserved unrelated field
    assert body["service_properties"]["keep_me"] == "yes"
    assert body["service_properties"]["logging_level"] == "DEBUG"


def test_logging_level_configured_writes_uppercase(logging_stub):
    st.logging_level_configured("audit-policy", service="policy", level="warning")
    _, body = logging_stub["puts"][0]
    assert body["service_properties"]["logging_level"] == "WARNING"


@pytest.mark.parametrize(
    "service",
    ["manager", "policy", "async_replicator", "http"],
)
def test_logging_level_configured_all_four_services(logging_stub, service):
    ret = st.logging_level_configured(f"audit-{service}", service=service, level="DEBUG")
    assert ret["result"] is True
    assert ret["changes"]["logging_level"]["new"] == "DEBUG"
    service_name, _ = logging_stub["puts"][-1]
    assert service_name == service


def test_logging_level_configured_rejects_unknown_service(logging_stub):
    ret = st.logging_level_configured("audit-bogus", service="bogus", level="INFO")
    assert ret["result"] is False
    assert "bogus" in ret["comment"]
    assert logging_stub["puts"] == []


def test_logging_level_configured_rejects_unknown_level(logging_stub):
    ret = st.logging_level_configured("audit-manager", service="manager", level="LOUD")
    assert ret["result"] is False
    assert "LOUD" in ret["comment"]
    assert logging_stub["puts"] == []


def test_logging_level_configured_test_mode(logging_stub, monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.logging_level_configured("audit-manager", service="manager", level="DEBUG")
    assert ret["result"] is None
    assert ret["changes"] == {"logging_level": {"old": "INFO", "new": "DEBUG"}}
    assert logging_stub["puts"] == []


def test_logging_level_configured_handles_missing_current(monkeypatch, logging_stub):
    """If current has no service_properties block at all, still writes cleanly."""

    def _empty_get(opts, service_name, profile=None):
        return {"service_name": service_name}

    monkeypatch.setattr(c, "service_get", _empty_get)

    ret = st.logging_level_configured("audit-manager", service="manager", level="INFO")
    assert ret["result"] is True
    assert ret["changes"] == {"logging_level": {"old": None, "new": "INFO"}}
    assert len(logging_stub["puts"]) == 1
    _, body = logging_stub["puts"][0]
    assert body["service_properties"]["logging_level"] == "INFO"
