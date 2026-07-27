"""Tests for the NSX telemetry / CEIP client."""

import responses

from saltext.vcf.clients import nsx_telemetry


def test_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/telemetry/config",
        json={"optin": True, "schedule_enabled": True},
        status=200,
    )
    result = nsx_telemetry.get(opts)
    assert result["optin"] is True


def test_update_puts_body(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/api/v1/telemetry/config",
        json={"optin": False},
        status=200,
    )
    result = nsx_telemetry.update(opts, optin=False)
    assert result == {"optin": False}


def test_set_optin_reads_then_puts(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/telemetry/config",
        json={"optin": True, "schedule_enabled": True, "proxy": "corp"},
        status=200,
    )
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/api/v1/telemetry/config",
        json={"optin": False, "schedule_enabled": True, "proxy": "corp"},
        status=200,
    )
    result = nsx_telemetry.set_optin(opts, False)
    assert result["optin"] is False
    # The PUT should preserve the other keys from the GET
    put_call = mocked_responses.calls[1]
    assert '"schedule_enabled": true' in put_call.request.body.decode()
    assert '"proxy": "corp"' in put_call.request.body.decode()
    assert '"optin": false' in put_call.request.body.decode()
