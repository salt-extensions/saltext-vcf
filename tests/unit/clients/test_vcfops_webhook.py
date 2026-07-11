"""Tests for clients.vcfops_webhook."""

import pytest
import requests
import responses

from saltext.vcf.clients import vcfops_webhook as wh

_INSTANCES = "https://ops.test/suite-api/api/outbound-instances"
_RULES = "https://ops.test/suite-api/api/notifications/rules"


# ---------------------------------------------------------------------------
# Outbound instances
# ---------------------------------------------------------------------------


def test_list_returns_payload(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _INSTANCES, json={"outboundInstances": []}, status=200)
    assert wh.list_(opts) == {"outboundInstances": []}


def test_list_sends_pagination(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _INSTANCES, json={"outboundInstances": []}, status=200)
    wh.list_(opts, page=2, page_size=50)
    url = vcfops_authed.calls[-1].request.url
    assert "page=2" in url
    assert "pageSize=50" in url


def test_get_returns_instance(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_INSTANCES}/wh-1", json={"id": "wh-1"}, status=200)
    assert wh.get(opts, "wh-1") == {"id": "wh-1"}


def test_get_or_none_returns_none_on_404(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_INSTANCES}/missing", status=404)
    assert wh.get_or_none(opts, "missing") is None


def test_get_or_none_propagates_other_errors(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_INSTANCES}/boom", status=500)
    with pytest.raises(requests.HTTPError):
        wh.get_or_none(opts, "boom")


def test_create_posts_spec(opts, vcfops_authed):
    vcfops_authed.add(responses.POST, _INSTANCES, json={"id": "wh-new"}, status=201)
    out = wh.create(
        opts,
        {
            "name": "pagerduty-prod",
            "pluginTypeId": "RestPlugin",
            "configValues": [{"name": "url", "value": "https://x/"}],
        },
    )
    assert out == {"id": "wh-new"}


def test_update_puts_spec(opts, vcfops_authed):
    vcfops_authed.add(responses.PUT, f"{_INSTANCES}/wh-1", json={"id": "wh-1"}, status=200)
    assert wh.update(opts, "wh-1", {"name": "updated"}) == {"id": "wh-1"}


def test_delete_calls_delete(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_INSTANCES}/wh-1", status=204)
    wh.delete(opts, "wh-1")
    assert vcfops_authed.calls[-1].request.method == "DELETE"


# ---------------------------------------------------------------------------
# Notification rules
# ---------------------------------------------------------------------------


def test_list_rules_returns_payload(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _RULES, json={"notificationRules": []}, status=200)
    assert wh.list_rules(opts) == {"notificationRules": []}


def test_list_rules_sends_pagination(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _RULES, json={"notificationRules": []}, status=200)
    wh.list_rules(opts, page=3, page_size=25)
    url = vcfops_authed.calls[-1].request.url
    assert "page=3" in url
    assert "pageSize=25" in url


def test_get_rule_returns_rule(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_RULES}/r-1", json={"id": "r-1"}, status=200)
    assert wh.get_rule(opts, "r-1") == {"id": "r-1"}


def test_get_rule_or_none_returns_none_on_404(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_RULES}/missing", status=404)
    assert wh.get_rule_or_none(opts, "missing") is None


def test_get_rule_or_none_propagates_other_errors(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{_RULES}/boom", status=500)
    with pytest.raises(requests.HTTPError):
        wh.get_rule_or_none(opts, "boom")


def test_create_rule_posts_spec(opts, vcfops_authed):
    vcfops_authed.add(responses.POST, _RULES, json={"id": "r-new"}, status=201)
    out = wh.create_rule(
        opts,
        {
            "name": "prod-critical-to-pagerduty",
            "pluginId": "wh-1",
            "alertControlStates": ["OPEN"],
            "alertCriticalities": ["CRITICAL"],
        },
    )
    assert out == {"id": "r-new"}


def test_update_rule_puts_spec(opts, vcfops_authed):
    vcfops_authed.add(responses.PUT, f"{_RULES}/r-1", json={"id": "r-1"}, status=200)
    assert wh.update_rule(opts, "r-1", {"name": "updated"}) == {"id": "r-1"}


def test_delete_rule_calls_delete(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_RULES}/r-1", status=204)
    wh.delete_rule(opts, "r-1")
    assert vcfops_authed.calls[-1].request.method == "DELETE"
