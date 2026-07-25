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
