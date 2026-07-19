"""Tests for VMSP clients (ntp/dns/syslog) and util token flow."""

import responses

from saltext.vcf.clients import vmsp_dns
from saltext.vcf.clients import vmsp_ntp
from saltext.vcf.clients import vmsp_syslog

COMPONENTS_URL = "https://vmsp.test/api/v1/components"


def _vsp_component(network=None, logs=None):
    return {
        "components": [
            {
                "id": "comp-vsp-1",
                "name": "vsp",
                "spec": {"configuration": {"network": network or {}, "logs": logs or {}}},
            }
        ]
    }


def test_ntp_get(opts, vmsp_authed):
    vmsp_authed.add(
        responses.GET,
        COMPONENTS_URL,
        json=_vsp_component(network={"ntpServers": ["10.0.0.250"]}),
        status=200,
    )
    assert vmsp_ntp.get(opts) == {"servers": ["10.0.0.250"]}


def test_dns_get(opts, vmsp_authed):
    vmsp_authed.add(
        responses.GET,
        COMPONENTS_URL,
        json=_vsp_component(network={"dnsServers": ["10.0.0.1"]}),
        status=200,
    )
    assert vmsp_dns.get(opts) == {"servers": ["10.0.0.1"]}


def test_syslog_get(opts, vmsp_authed):
    vmsp_authed.add(
        responses.GET,
        COMPONENTS_URL,
        json=_vsp_component(logs={"syslog": {"host": "s.test", "port": 514}}),
        status=200,
    )
    assert vmsp_syslog.get(opts) == {"syslog": {"host": "s.test", "port": 514}}


def test_ntp_set_applies_and_waits(opts, vmsp_authed):
    vmsp_authed.add(responses.GET, COMPONENTS_URL, json=_vsp_component(), status=200)
    vmsp_authed.add(
        responses.POST,
        "https://vmsp.test/api/v1/components/comp-vsp-1",
        json={"id": "task-1"},
        status=200,
    )
    vmsp_authed.add(
        responses.GET,
        "https://vmsp.test/api/v1/tasks/task-1",
        json={"phase": "Succeeded", "status": "Succeeded"},
        status=200,
    )
    result = vmsp_ntp.set_(opts, ["10.0.0.250"])
    assert result["phase"] == "Succeeded"
    apply_call = [c for c in vmsp_authed.calls if c.request.method == "POST" and "components/comp-vsp-1" in c.request.url][0]
    assert b'"ntpServers"' in apply_call.request.body
    assert b"10.0.0.250" in apply_call.request.body


def test_component_not_found_raises(opts, vmsp_authed):
    vmsp_authed.add(responses.GET, COMPONENTS_URL, json={"components": []}, status=200)
    try:
        vmsp_ntp.get(opts)
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("expected ValueError when vsp component is absent")
