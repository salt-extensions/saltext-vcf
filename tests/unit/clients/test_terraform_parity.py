"""Unit tests for the Terraform-parity batch.

Covers the REST clients added in:
 - NSX QoS profile
 - NSX L2 VPN
 - NSX IDS/IPS
 - vCenter compute policy
 - vCenter LCM depot

SOAP clients (cluster overrides, datastore cluster, host datastore) live in
``test_terraform_parity_soap.py`` to keep the mocking strategies separate.
"""

from __future__ import annotations

import json

import responses

from saltext.vcf.clients import nsx_ids
from saltext.vcf.clients import nsx_l2_vpn
from saltext.vcf.clients import nsx_qos_profile
from saltext.vcf.clients import vcenter_compute_policy
from saltext.vcf.clients import vcenter_lcm_depot

NSX_BASE = "https://nsx.test"
INFRA = f"{NSX_BASE}/policy/api/v1/infra"
T0 = "vmc"
LOC = "default"


# ---------------------------------------------------------------------------
# NSX QoS profile
# ---------------------------------------------------------------------------


def test_qos_profile_crud(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/qos-profiles", json={"results": []}, status=200)
    mocked_responses.add(responses.PUT, f"{INFRA}/qos-profiles/q-1", json={"id": "q-1"}, status=200)
    mocked_responses.add(responses.DELETE, f"{INFRA}/qos-profiles/q-1", json=None, status=200)
    nsx_qos_profile.list_(opts)
    nsx_qos_profile.create(opts, "q-1", class_of_service=3)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"display_name": "q-1", "class_of_service": 3}
    nsx_qos_profile.delete(opts, "q-1")


def test_qos_profile_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/qos-profiles/missing", status=404)
    assert nsx_qos_profile.get_or_none(opts, "missing") is None


# ---------------------------------------------------------------------------
# NSX L2 VPN
# ---------------------------------------------------------------------------


def test_l2_vpn_service_crud(opts, mocked_responses):
    base = f"{INFRA}/tier-0s/{T0}/locale-services/{LOC}/l2vpn-services"
    mocked_responses.add(responses.GET, base, json={"results": []}, status=200)
    mocked_responses.add(responses.PUT, f"{base}/svc-1", json={"id": "svc-1"}, status=200)
    mocked_responses.add(responses.DELETE, f"{base}/svc-1", json=None, status=200)
    nsx_l2_vpn.list_services(opts, T0, LOC)
    nsx_l2_vpn.create_service(opts, T0, LOC, "svc-1", mode="SERVER")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "L2VPNService"
    assert body["mode"] == "SERVER"
    nsx_l2_vpn.delete_service(opts, T0, LOC, "svc-1")


def test_l2_vpn_session_crud(opts, mocked_responses):
    sess_url = f"{INFRA}/tier-0s/{T0}/locale-services/{LOC}/l2vpn-services/svc-1/sessions/s-1"
    mocked_responses.add(responses.PUT, sess_url, json={"id": "s-1"}, status=200)
    mocked_responses.add(responses.DELETE, sess_url, json=None, status=200)
    nsx_l2_vpn.create_session(
        opts, T0, LOC, "svc-1", "s-1", transport_tunnels=["/path/to/ipsec-session"]
    )
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "L2VPNSession"
    assert body["transport_tunnels"] == ["/path/to/ipsec-session"]
    nsx_l2_vpn.delete_session(opts, T0, LOC, "svc-1", "s-1")


def test_l2_vpn_get_or_none_404(opts, mocked_responses):
    base = f"{INFRA}/tier-0s/{T0}/locale-services/{LOC}/l2vpn-services"
    mocked_responses.add(responses.GET, f"{base}/missing", status=404)
    mocked_responses.add(responses.GET, f"{base}/svc-1/sessions/missing", status=404)
    assert nsx_l2_vpn.get_service_or_none(opts, T0, LOC, "missing") is None
    assert nsx_l2_vpn.get_session_or_none(opts, T0, LOC, "svc-1", "missing") is None


# ---------------------------------------------------------------------------
# NSX IDS/IPS
# ---------------------------------------------------------------------------


def test_ids_global_config(opts, mocked_responses):
    url = f"{INFRA}/settings/firewall/security/intrusion-services"
    mocked_responses.add(responses.GET, url, json={"auto_update": True}, status=200)
    mocked_responses.add(responses.PUT, url, json={"auto_update": False}, status=200)
    assert nsx_ids.get_global_config(opts)["auto_update"] is True
    nsx_ids.set_global_config(opts, auto_update=False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "IdsGlobalConfig"
    assert body["auto_update"] is False


def test_ids_cluster_config_crud(opts, mocked_responses):
    base = f"{INFRA}/settings/firewall/security/intrusion-services/cluster-configs"
    mocked_responses.add(responses.GET, base, json={"results": []}, status=200)
    mocked_responses.add(responses.PUT, f"{base}/cl-1", json={"ids_enabled": True}, status=200)
    nsx_ids.list_cluster_configs(opts)
    nsx_ids.set_cluster_config(opts, "cl-1", ids_enabled=True)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "IdsClusterConfig"
    assert body["ids_enabled"] is True


def test_ids_profile_crud(opts, mocked_responses):
    base = f"{INFRA}/settings/firewall/security/intrusion-services/profiles"
    mocked_responses.add(responses.PUT, f"{base}/p-1", json={"id": "p-1"}, status=200)
    mocked_responses.add(responses.DELETE, f"{base}/p-1", json=None, status=200)
    nsx_ids.create_profile(opts, "p-1", severities=["CRITICAL"])
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "IdsProfile"
    assert body["display_name"] == "p-1"
    assert body["severities"] == ["CRITICAL"]
    nsx_ids.delete_profile(opts, "p-1")


def test_ids_policy_and_rule_crud(opts, mocked_responses):
    policy_url = f"{INFRA}/domains/default/intrusion-service-policies/sp-1"
    rule_url = f"{policy_url}/rules/r-1"
    mocked_responses.add(responses.PUT, policy_url, json={"id": "sp-1"}, status=200)
    mocked_responses.add(responses.PUT, rule_url, json={"id": "r-1"}, status=200)
    mocked_responses.add(responses.DELETE, rule_url, json=None, status=200)
    mocked_responses.add(responses.DELETE, policy_url, json=None, status=200)
    nsx_ids.create_policy(opts, "sp-1", category="Infrastructure")
    nsx_ids.create_rule(opts, "r-1", "sp-1", action="DETECT", ids_profiles=["/path/to/p"])
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "r-1"
    assert body["action"] == "DETECT"
    nsx_ids.delete_rule(opts, "r-1", "sp-1")
    nsx_ids.delete_policy(opts, "sp-1")


def test_ids_get_or_none_404(opts, mocked_responses):
    base = f"{INFRA}/settings/firewall/security/intrusion-services"
    mocked_responses.add(responses.GET, f"{base}/cluster-configs/missing", status=404)
    mocked_responses.add(responses.GET, f"{base}/profiles/missing", status=404)
    mocked_responses.add(
        responses.GET,
        f"{INFRA}/domains/default/intrusion-service-policies/missing",
        status=404,
    )
    mocked_responses.add(
        responses.GET,
        f"{INFRA}/domains/default/intrusion-service-policies/sp-1/rules/missing",
        status=404,
    )
    assert nsx_ids.get_cluster_config_or_none(opts, "missing") is None
    assert nsx_ids.get_profile_or_none(opts, "missing") is None
    assert nsx_ids.get_policy_or_none(opts, "missing") is None
    assert nsx_ids.get_rule_or_none(opts, "missing", "sp-1") is None


# ---------------------------------------------------------------------------
# vCenter compute policy
# ---------------------------------------------------------------------------

VC = "https://vc.test"


def test_compute_policy_crud(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{VC}/api/vcenter/vm/compute/policies", json=[], status=200)
    vcenter_authed.add(
        responses.POST, f"{VC}/api/vcenter/vm/compute/policies", json="pol-1", status=200
    )
    vcenter_authed.add(
        responses.DELETE, f"{VC}/api/vcenter/vm/compute/policies/pol-1", json=None, status=200
    )
    vcenter_compute_policy.list_(opts)
    assert (
        vcenter_compute_policy.create(
            opts,
            "com.vmware.vcenter.compute.policies.capabilities.vm.vm_anti_affinity",
            name="anti-affinity",
            vm_tag="db",
        )
        == "pol-1"
    )
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["capability"].endswith("vm_anti_affinity")
    assert body["name"] == "anti-affinity"
    vcenter_compute_policy.delete(opts, "pol-1")


def test_compute_policy_get_or_none_404(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{VC}/api/vcenter/vm/compute/policies/missing", status=404)
    assert vcenter_compute_policy.get_or_none(opts, "missing") is None


# ---------------------------------------------------------------------------
# vCenter LCM depot
# ---------------------------------------------------------------------------


def test_lcm_depot_offline_crud(opts, vcenter_authed):
    base = f"{VC}/api/esx/settings/depots/offline"
    vcenter_authed.add(responses.GET, base, json=[], status=200)
    vcenter_authed.add(responses.POST, base, json="dep-1", status=200)
    vcenter_authed.add(responses.DELETE, f"{base}/dep-1", json=None, status=200)
    vcenter_lcm_depot.list_offline(opts)
    new_id = vcenter_lcm_depot.create_offline(opts, "/storage/updatemgr/foo.zip")
    assert new_id == "dep-1"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["file_locator"] == "/storage/updatemgr/foo.zip"
    vcenter_lcm_depot.delete_offline(opts, "dep-1")


def test_lcm_depot_online_crud(opts, vcenter_authed):
    base = f"{VC}/api/esx/settings/depots/online"
    vcenter_authed.add(responses.POST, base, json="dep-2", status=200)
    vcenter_lcm_depot.create_online(opts, "https://hostupdate.vmware.com/", description="vmw")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["location"] == "https://hostupdate.vmware.com/"
    assert body["description"] == "vmw"


def test_lcm_depot_sync_action(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{VC}/api/esx/settings/depots", json="task-1", status=200)
    vcenter_lcm_depot.sync(opts)
    assert "action=sync" in vcenter_authed.calls[-1].request.url


def test_lcm_depot_get_or_none_404(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{VC}/api/esx/settings/depots/offline/missing", status=404)
    assert vcenter_lcm_depot.get_offline_or_none(opts, "missing") is None
