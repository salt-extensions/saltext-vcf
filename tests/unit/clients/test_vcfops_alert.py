"""Tests for clients.vcfops_alert CRUD on alert + symptom definitions."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import vcfops_alert as a

_ALERTS = "https://ops.test/suite-api/api/alertdefinitions"
_SYMPTOMS = "https://ops.test/suite-api/api/symptomdefinitions"


# ---------------------------------------------------------------------------
# alert definitions — create
# ---------------------------------------------------------------------------


def test_alerts_create_posts_body(opts, vcfops_authed):
    spec = {
        "name": "High CPU",
        "description": "cpu > 90 for 15m",
        "adapterKindKey": "VMWARE",
        "resourceKindKey": "HostSystem",
        "waitCycles": 1,
        "cancelCycles": 1,
        "type": 16,
        "subType": 19,
        "states": [
            {
                "impact": {"impactType": "RISK"},
                "severity": "CRITICAL",
                "base-symptom-set": {
                    "type": "SYMPTOM_SET",
                    "relation": "SELF",
                    "aggregation": "ALL",
                    "symptomSetOperator": "AND",
                    "symptomDefinitionIds": ["SymptomDefinition-1"],
                },
            }
        ],
    }
    echoed = dict(spec, id="AlertDefinition-99")
    vcfops_authed.add(responses.POST, _ALERTS, json=echoed, status=201)

    out = a.alerts_create(opts, spec)

    assert out == echoed
    last = vcfops_authed.calls[-1].request
    assert last.method == "POST"
    assert last.url == _ALERTS
    assert json.loads(last.body) == spec


def test_alerts_create_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.POST, _ALERTS, json={"message": "boom"}, status=400)
    with pytest.raises(requests.HTTPError):
        a.alerts_create(opts, {"name": "x"})


# ---------------------------------------------------------------------------
# alert definitions — update
# ---------------------------------------------------------------------------


def test_alerts_update_puts_body_to_id(opts, vcfops_authed):
    spec = {"id": "AlertDefinition-1", "name": "Renamed", "waitCycles": 2}
    vcfops_authed.add(responses.PUT, f"{_ALERTS}/AlertDefinition-1", json=spec, status=200)

    out = a.alerts_update(opts, "AlertDefinition-1", spec)

    assert out == spec
    last = vcfops_authed.calls[-1].request
    assert last.method == "PUT"
    assert last.url == f"{_ALERTS}/AlertDefinition-1"
    assert json.loads(last.body) == spec


def test_alerts_update_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.PUT, f"{_ALERTS}/bad", json={"message": "boom"}, status=500)
    with pytest.raises(requests.HTTPError):
        a.alerts_update(opts, "bad", {"id": "bad"})


# ---------------------------------------------------------------------------
# alert definitions — delete
# ---------------------------------------------------------------------------


def test_alerts_delete_issues_delete_and_returns_empty(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_ALERTS}/AlertDefinition-1", status=204)

    out = a.alerts_delete(opts, "AlertDefinition-1")

    assert out == {}
    last = vcfops_authed.calls[-1].request
    assert last.method == "DELETE"
    assert last.url == f"{_ALERTS}/AlertDefinition-1"


def test_alerts_delete_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_ALERTS}/bad", json={"message": "boom"}, status=500)
    with pytest.raises(requests.HTTPError):
        a.alerts_delete(opts, "bad")


# ---------------------------------------------------------------------------
# symptom definitions — create
# ---------------------------------------------------------------------------


def test_symptoms_create_posts_body(opts, vcfops_authed):
    spec = {
        "name": "CPU > 90",
        "adapterKindKey": "VMWARE",
        "resourceKindKey": "HostSystem",
        "waitCycles": 1,
        "cancelCycles": 1,
        "state": {
            "severity": "CRITICAL",
            "condition": {
                "type": "CONDITION_HT",
                "key": "cpu|usage_average",
                "operator": "GT",
                "value": "90",
                "valueType": "NUMERIC",
                "instanced": False,
                "thresholdType": "STATIC",
            },
        },
    }
    echoed = dict(spec, id="SymptomDefinition-99")
    vcfops_authed.add(responses.POST, _SYMPTOMS, json=echoed, status=201)

    out = a.symptoms_create(opts, spec)

    assert out == echoed
    last = vcfops_authed.calls[-1].request
    assert last.method == "POST"
    assert last.url == _SYMPTOMS
    assert json.loads(last.body) == spec


def test_symptoms_create_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.POST, _SYMPTOMS, json={"message": "boom"}, status=400)
    with pytest.raises(requests.HTTPError):
        a.symptoms_create(opts, {"name": "x"})


# ---------------------------------------------------------------------------
# symptom definitions — update
# ---------------------------------------------------------------------------


def test_symptoms_update_puts_body_to_id(opts, vcfops_authed):
    spec = {"id": "SymptomDefinition-1", "name": "Renamed"}
    vcfops_authed.add(responses.PUT, f"{_SYMPTOMS}/SymptomDefinition-1", json=spec, status=200)

    out = a.symptoms_update(opts, "SymptomDefinition-1", spec)

    assert out == spec
    last = vcfops_authed.calls[-1].request
    assert last.method == "PUT"
    assert last.url == f"{_SYMPTOMS}/SymptomDefinition-1"
    assert json.loads(last.body) == spec


def test_symptoms_update_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.PUT, f"{_SYMPTOMS}/bad", json={"message": "boom"}, status=500)
    with pytest.raises(requests.HTTPError):
        a.symptoms_update(opts, "bad", {"id": "bad"})


# ---------------------------------------------------------------------------
# symptom definitions — delete
# ---------------------------------------------------------------------------


def test_symptoms_delete_issues_delete_and_returns_empty(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_SYMPTOMS}/SymptomDefinition-1", status=204)

    out = a.symptoms_delete(opts, "SymptomDefinition-1")

    assert out == {}
    last = vcfops_authed.calls[-1].request
    assert last.method == "DELETE"
    assert last.url == f"{_SYMPTOMS}/SymptomDefinition-1"


def test_symptoms_delete_propagates_http_error(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, f"{_SYMPTOMS}/bad", json={"message": "boom"}, status=500)
    with pytest.raises(requests.HTTPError):
        a.symptoms_delete(opts, "bad")
