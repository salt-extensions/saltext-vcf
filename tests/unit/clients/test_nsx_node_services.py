"""Tests for the NSX node-services client (HTTP service config)."""

import json

import responses

from saltext.vcf.clients import nsx_node_services

URL = "https://nsx.test/api/v1/node/services/http"


def test_http_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        URL,
        json={
            "service_name": "http",
            "service_properties": {
                "client_api_rate_limit": 40,
                "client_api_concurrency_limit": 20,
                "global_api_concurrency_limit": 199,
                "connection_timeout": 30,
                "redirect_host": "mgmt-nsx.example.test",
            },
        },
        status=200,
    )
    got = nsx_node_services.http_get(opts)
    assert got["service_properties"]["client_api_rate_limit"] == 40


def test_http_put(opts, mocked_responses):
    body = {"service_name": "http", "service_properties": {"client_api_rate_limit": 100}}
    mocked_responses.add(responses.PUT, URL, json=body, status=200)
    nsx_node_services.http_put(opts, body)
    assert mocked_responses.calls[0].request.url == URL
    assert (
        json.loads(mocked_responses.calls[0].request.body)["service_properties"][
            "client_api_rate_limit"
        ]
        == 100
    )


def test_http_set_merges_over_current(opts, mocked_responses):
    """http_set must GET-then-PUT so unrelated fields survive the total-replace."""
    mocked_responses.add(
        responses.GET,
        URL,
        json={
            "service_name": "http",
            "service_properties": {
                "client_api_rate_limit": 40,
                "client_api_concurrency_limit": 20,
                "global_api_concurrency_limit": 199,
                "connection_timeout": 30,
                "redirect_host": "keep-me.example.test",
                "cipher_suites": [{"name": "TLS_AES_256_GCM_SHA384", "enabled": True}],
            },
        },
        status=200,
    )
    mocked_responses.add(responses.PUT, URL, json={"ok": True}, status=200)

    nsx_node_services.http_set(
        opts,
        client_api_rate_limit=100,
        client_api_concurrency_limit=40,
    )

    put_call = mocked_responses.calls[1]
    sent = json.loads(put_call.request.body)
    props = sent["service_properties"]
    # Updated fields
    assert props["client_api_rate_limit"] == 100
    assert props["client_api_concurrency_limit"] == 40
    # Untouched fields preserved
    assert props["global_api_concurrency_limit"] == 199
    assert props["redirect_host"] == "keep-me.example.test"
    assert props["connection_timeout"] == 30
    assert props["cipher_suites"] == [{"name": "TLS_AES_256_GCM_SHA384", "enabled": True}]


def test_http_set_drops_none_fields(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        URL,
        json={"service_properties": {"client_api_rate_limit": 40}},
        status=200,
    )
    mocked_responses.add(responses.PUT, URL, json={}, status=200)

    nsx_node_services.http_set(opts, client_api_rate_limit=100, redirect_host=None)

    sent = json.loads(mocked_responses.calls[1].request.body)
    # None-valued kwarg must not be written
    assert "redirect_host" not in sent["service_properties"]
    assert sent["service_properties"]["client_api_rate_limit"] == 100


# ---------------------------------------------------------------------------
# Generic ``service_*`` verbs + audit-logging service wrappers
# ---------------------------------------------------------------------------


import pytest  # noqa: E402


@pytest.mark.parametrize(
    "service_name",
    ["async_replicator", "http", "manager", "policy"],
)
def test_service_get_hits_expected_path(opts, mocked_responses, service_name):
    url = f"https://nsx.test/api/v1/node/services/{service_name}"
    mocked_responses.add(
        responses.GET,
        url,
        json={
            "service_name": service_name,
            "service_properties": {"logging_level": "INFO"},
        },
        status=200,
    )
    got = nsx_node_services.service_get(opts, service_name)
    assert got["service_properties"]["logging_level"] == "INFO"
    assert mocked_responses.calls[0].request.url == url


@pytest.mark.parametrize(
    "service_name",
    ["async_replicator", "manager", "policy"],
)
def test_service_set_merges_over_current(opts, mocked_responses, service_name):
    """service_set must GET-then-PUT so unrelated fields survive the total-replace."""
    url = f"https://nsx.test/api/v1/node/services/{service_name}"
    mocked_responses.add(
        responses.GET,
        url,
        json={
            "service_name": service_name,
            "service_properties": {
                "logging_level": "INFO",
                "keep_me": "yes",
            },
        },
        status=200,
    )
    mocked_responses.add(responses.PUT, url, json={"ok": True}, status=200)

    nsx_node_services.service_set(opts, service_name, logging_level="DEBUG")

    put_call = mocked_responses.calls[1]
    assert put_call.request.url == url
    sent = json.loads(put_call.request.body)
    props = sent["service_properties"]
    assert props["logging_level"] == "DEBUG"
    # Untouched fields preserved
    assert props["keep_me"] == "yes"


def test_service_set_drops_none_fields(opts, mocked_responses):
    url = "https://nsx.test/api/v1/node/services/manager"
    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    mocked_responses.add(responses.PUT, url, json={}, status=200)

    nsx_node_services.service_set(opts, "manager", logging_level="DEBUG", other=None)

    sent = json.loads(mocked_responses.calls[1].request.body)
    assert "other" not in sent["service_properties"]
    assert sent["service_properties"]["logging_level"] == "DEBUG"


def test_manager_wrappers_hit_manager_path(opts, mocked_responses):
    url = "https://nsx.test/api/v1/node/services/manager"
    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    mocked_responses.add(responses.PUT, url, json={}, status=200)

    got = nsx_node_services.manager_get(opts)
    assert got["service_properties"]["logging_level"] == "INFO"

    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    nsx_node_services.manager_set(opts, logging_level="WARNING")
    put_call = mocked_responses.calls[-1]
    assert put_call.request.url == url
    assert json.loads(put_call.request.body)["service_properties"]["logging_level"] == "WARNING"


def test_policy_wrappers_hit_policy_path(opts, mocked_responses):
    url = "https://nsx.test/api/v1/node/services/policy"
    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    mocked_responses.add(responses.PUT, url, json={}, status=200)

    nsx_node_services.policy_get(opts)
    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    nsx_node_services.policy_set(opts, logging_level="ERROR")
    put_call = mocked_responses.calls[-1]
    assert put_call.request.url == url
    assert json.loads(put_call.request.body)["service_properties"]["logging_level"] == "ERROR"


def test_async_replicator_wrappers_hit_async_replicator_path(opts, mocked_responses):
    url = "https://nsx.test/api/v1/node/services/async_replicator"
    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    mocked_responses.add(responses.PUT, url, json={}, status=200)

    nsx_node_services.async_replicator_get(opts)
    mocked_responses.add(
        responses.GET,
        url,
        json={"service_properties": {"logging_level": "INFO"}},
        status=200,
    )
    nsx_node_services.async_replicator_set(opts, logging_level="DEBUG")
    put_call = mocked_responses.calls[-1]
    assert put_call.request.url == url
    assert json.loads(put_call.request.body)["service_properties"]["logging_level"] == "DEBUG"


def test_logging_services_constant_matches_stig_912():
    assert nsx_node_services.LOGGING_SERVICES == (
        "async_replicator",
        "http",
        "manager",
        "policy",
    )
