"""Tests for the NSX IPsec VPN clients (T7)."""

import json

import responses

from saltext.vmware.clients import nsx_ipsec_vpn

BASE = "https://nsx.test"
INFRA = f"{BASE}/policy/api/v1/infra"
T0 = "vmc"
LOC = "default"
SVC_BASE = f"{INFRA}/tier-0s/{T0}/locale-services/{LOC}/ipsec-vpn-services"


def test_ike_profile_crud(opts, mocked_responses):
    mocked_responses.add(
        responses.GET, f"{INFRA}/ipsec-vpn-ike-profiles", json={"results": []}, status=200
    )
    mocked_responses.add(
        responses.PUT,
        f"{INFRA}/ipsec-vpn-ike-profiles/ike-1",
        json={"id": "ike-1"},
        status=200,
    )
    mocked_responses.add(
        responses.DELETE, f"{INFRA}/ipsec-vpn-ike-profiles/ike-1", json=None, status=200
    )
    nsx_ipsec_vpn.list_ike_profiles(opts)
    nsx_ipsec_vpn.create_ike_profile(
        opts, "ike-1", ike_version="IKE_V2", encryption_algorithms=["AES_GCM_128"]
    )
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "ike-1"
    assert body["ike_version"] == "IKE_V2"
    nsx_ipsec_vpn.delete_ike_profile(opts, "ike-1")


def test_tunnel_profile_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        f"{INFRA}/ipsec-vpn-tunnel-profiles/t-1",
        json={"id": "t-1"},
        status=200,
    )
    nsx_ipsec_vpn.create_tunnel_profile(opts, "t-1", df_policy="COPY")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "t-1"
    assert body["df_policy"] == "COPY"


def test_dpd_profile_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT, f"{INFRA}/ipsec-vpn-dpd-profiles/d-1", json={"id": "d-1"}, status=200
    )
    nsx_ipsec_vpn.create_dpd_profile(opts, "d-1", dpd_probe_interval=10)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["dpd_probe_interval"] == 10


def test_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/ipsec-vpn-ike-profiles/missing", status=404)
    mocked_responses.add(responses.GET, f"{INFRA}/ipsec-vpn-tunnel-profiles/missing", status=404)
    mocked_responses.add(responses.GET, f"{INFRA}/ipsec-vpn-dpd-profiles/missing", status=404)
    assert nsx_ipsec_vpn.get_ike_profile_or_none(opts, "missing") is None
    assert nsx_ipsec_vpn.get_tunnel_profile_or_none(opts, "missing") is None
    assert nsx_ipsec_vpn.get_dpd_profile_or_none(opts, "missing") is None


def test_service_crud(opts, mocked_responses):
    mocked_responses.add(responses.GET, SVC_BASE, json={"results": []}, status=200)
    mocked_responses.add(responses.PUT, f"{SVC_BASE}/svc-1", json={"id": "svc-1"}, status=200)
    mocked_responses.add(responses.DELETE, f"{SVC_BASE}/svc-1", json=None, status=200)
    nsx_ipsec_vpn.list_services(opts, T0, LOC)
    nsx_ipsec_vpn.create_service(opts, T0, LOC, "svc-1", enabled=True)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "IPSecVpnService"
    assert body["display_name"] == "svc-1"
    assert body["enabled"] is True
    nsx_ipsec_vpn.delete_service(opts, T0, LOC, "svc-1")


def test_service_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{SVC_BASE}/missing", status=404)
    assert nsx_ipsec_vpn.get_service_or_none(opts, T0, LOC, "missing") is None


def test_session_crud(opts, mocked_responses):
    sess_url = f"{SVC_BASE}/svc-1/sessions/s-1"
    mocked_responses.add(
        responses.GET, f"{SVC_BASE}/svc-1/sessions", json={"results": []}, status=200
    )
    mocked_responses.add(responses.PUT, sess_url, json={"id": "s-1"}, status=200)
    mocked_responses.add(responses.DELETE, sess_url, json=None, status=200)
    nsx_ipsec_vpn.list_sessions(opts, T0, LOC, "svc-1")
    nsx_ipsec_vpn.create_session(
        opts,
        T0,
        LOC,
        "svc-1",
        "s-1",
        "PolicyBasedIPSecVpnSession",
        peer_address="203.0.113.1",
        peer_id="203.0.113.1",
    )
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "PolicyBasedIPSecVpnSession"
    assert body["peer_address"] == "203.0.113.1"
    nsx_ipsec_vpn.delete_session(opts, T0, LOC, "svc-1", "s-1")


def test_session_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{SVC_BASE}/svc-1/sessions/missing", status=404)
    assert nsx_ipsec_vpn.get_session_or_none(opts, T0, LOC, "svc-1", "missing") is None


def test_module_wrappers_delegate(opts, monkeypatch, mocked_responses):
    from saltext.vmware.modules import vmware_nsx_ipsec_vpn as m

    monkeypatch.setattr(m, "__opts__", opts, raising=False)

    mocked_responses.add(
        responses.GET, f"{INFRA}/ipsec-vpn-ike-profiles", json={"results": []}, status=200
    )
    mocked_responses.add(responses.PUT, f"{SVC_BASE}/svc-x", json={"id": "svc-x"}, status=200)
    m.list_ike_profiles()
    m.create_service(T0, LOC, "svc-x", enabled=False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["enabled"] is False
