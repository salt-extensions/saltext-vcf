"""Tests for the NSX Manager node NTP config client."""

import json

import pytest
import responses

from saltext.vcf.clients import nsx_ntp_servers

URL = "https://nsx.test/api/v1/node/services/ntp"


def service(start_on_boot=True):
    return {
        "_schema": "NodeNtpServiceProperties",
        "_self": {"href": "/node/services/ntp", "rel": "self"},
        "service_name": "ntp",
        "service_properties": {
            "servers": ["bifrost.vcf.nimbus.internal"],
            "start_on_boot": start_on_boot,
        },
    }


def test_ntp_get(opts, mocked_responses):
    mocked_responses.add(responses.GET, URL, json=service(), status=200)
    assert nsx_ntp_servers.ntp_get(opts) == {
        "ntp_servers": ["bifrost.vcf.nimbus.internal"]
    }


@pytest.mark.parametrize("start_on_boot", [True, False])
def test_ntp_set_preserves_service_properties(opts, mocked_responses, start_on_boot):
    current = service(start_on_boot)
    mocked_responses.add(responses.GET, URL, json=current, status=200)
    mocked_responses.add(responses.PUT, URL, json={}, status=200)
    nsx_ntp_servers.ntp_set(opts, ["time.example.test"])
    sent = json.loads(mocked_responses.calls[1].request.body)
    assert sent == {
        "service_name": "ntp",
        "service_properties": {
            "servers": ["time.example.test"],
            "start_on_boot": start_on_boot,
        },
    }


@pytest.mark.parametrize("body", [[], {}, {"service_properties": {}},
    {"service_properties": {"servers": "not-a-list"}}])
def test_malformed_response_does_not_write(opts, mocked_responses, body):
    mocked_responses.add(responses.GET, URL, json=body, status=200)
    with pytest.raises(ValueError):
        nsx_ntp_servers.ntp_set(opts, ["time.example.test"])
    assert len(mocked_responses.calls) == 1


def test_reject_string_servers(opts, mocked_responses):
    with pytest.raises(ValueError, match="servers must be a list"):
        nsx_ntp_servers.ntp_set(opts, "time.example.test")
    assert not mocked_responses.calls
