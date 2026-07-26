"""Tests for clients.sddc_ceip."""

import json

import responses

from saltext.vcf.clients import sddc_ceip

SM = "https://sm.test"


def test_get_returns_raw_body(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/system/ceip",
        json={"status": "ENABLED", "instanceId": "abc-123"},
        status=200,
    )
    body = sddc_ceip.get(opts)
    assert body == {"status": "ENABLED", "instanceId": "abc-123"}


def test_status_returns_string(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/system/ceip",
        json={"status": "DISABLED", "instanceId": "abc-123"},
        status=200,
    )
    assert sddc_ceip.status(opts) == "DISABLED"


def test_is_enabled_true_only_for_enabled(opts, sddc_authed):
    for state, expected in [
        ("ENABLED", True),
        ("DISABLED", False),
        ("DISABLING", False),
        ("ENABLING", False),
        ("DISABLING_FAILED", False),
        ("ENABLING_FAILED", False),
    ]:
        sddc_authed.add(
            responses.GET,
            f"{SM}/v1/system/ceip",
            json={"status": state, "instanceId": "x"},
            status=200,
        )
        assert sddc_ceip.is_enabled(opts) is expected, state


def test_set_true_sends_enable(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/system/ceip",
        json={"id": "task-1", "status": "IN_PROGRESS"},
        status=202,
    )
    result = sddc_ceip.set_(opts, True)
    assert result == {"id": "task-1", "status": "IN_PROGRESS"}
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"status": "ENABLE"}


def test_set_false_sends_disable(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/system/ceip",
        json={"id": "task-2", "status": "IN_PROGRESS"},
        status=202,
    )
    result = sddc_ceip.set_(opts, False)
    assert result["id"] == "task-2"
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"status": "DISABLE"}


def test_enable_helper(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/system/ceip",
        json={"id": "t", "status": "IN_PROGRESS"},
        status=202,
    )
    sddc_ceip.enable(opts)
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"status": "ENABLE"}


def test_disable_helper(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/system/ceip",
        json={"id": "t", "status": "IN_PROGRESS"},
        status=202,
    )
    sddc_ceip.disable(opts)
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"status": "DISABLE"}


def test_set_coerces_truthy_to_enable(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/system/ceip",
        json={"id": "t", "status": "IN_PROGRESS"},
        status=202,
    )
    sddc_ceip.set_(opts, 1)
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"status": "ENABLE"}
