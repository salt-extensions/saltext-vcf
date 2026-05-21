"""Cross-resource tests for the shared get_or_none idempotency helper.

These tests assert that every resource module's ``get_or_none`` swallows 404s
(returning ``None``) and lets other errors propagate. Pinning this behavior
here means state modules don't need to reimplement the pattern.

The ESXi clients use pyVmomi SOAP rather than REST, so their ``get_or_none``
behavior is exercised separately at the bottom of this file.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
import responses

from saltext.vcf.clients import esxi_advanced
from saltext.vcf.clients import esxi_firewall
from saltext.vcf.clients import esxi_service
from saltext.vcf.clients import nsx_compute_collection
from saltext.vcf.clients import nsx_context_profile
from saltext.vcf.clients import nsx_group
from saltext.vcf.clients import nsx_role_binding
from saltext.vcf.clients import nsx_security_policy
from saltext.vcf.clients import nsx_segment
from saltext.vcf.clients import nsx_service
from saltext.vcf.clients import nsx_tier0
from saltext.vcf.clients import nsx_tier1
from saltext.vcf.clients import nsx_transport_node
from saltext.vcf.clients import nsx_transport_zone
from saltext.vcf.clients import sddc_cluster
from saltext.vcf.clients import sddc_domain
from saltext.vcf.clients import sddc_host
from saltext.vcf.clients import sddc_vcf_services
from saltext.vcf.clients import vcenter_cluster
from saltext.vcf.clients import vcenter_datacenter
from saltext.vcf.clients import vcenter_datastore
from saltext.vcf.clients import vcenter_host
from saltext.vcf.clients import vcenter_supervisor_service
from saltext.vcf.clients import vcenter_supervisor_software
from saltext.vcf.clients import vcenter_tag
from saltext.vcf.clients import vcenter_vm
from saltext.vcf.clients import vcenter_vm_class
from saltext.vcf.clients import vcfops_adapter
from saltext.vcf.clients import vcfops_collector
from saltext.vcf.clients import vcfops_credential
from saltext.vcf.clients import vcfops_maintenance
from saltext.vcf.clients import vcfops_policy
from saltext.vcf.clients import vcfops_recommendation
from saltext.vcf.clients import vcfops_report
from saltext.vcf.clients import vcfops_resource
from saltext.vcf.clients import vcfops_resource_group
from saltext.vcf.clients import vcfops_solution
from saltext.vcf.clients import vcfops_supermetric
from saltext.vcf.clients import vcfops_task

# (resource module, endpoint URL, requires_auth_fixture_name)
VC_AUTH = "vcenter_authed"
SM_AUTH = "sddc_authed"
NX_AUTH = "mocked_responses"
OPS_AUTH = "vcfops_authed"

CASES = [
    (vcenter_cluster, "https://vc.test/api/vcenter/cluster/x", VC_AUTH),
    (vcenter_host, "https://vc.test/api/vcenter/host/x", VC_AUTH),
    (vcenter_vm, "https://vc.test/api/vcenter/vm/x", VC_AUTH),
    (vcenter_datacenter, "https://vc.test/api/vcenter/datacenter/x", VC_AUTH),
    (vcenter_datastore, "https://vc.test/api/vcenter/datastore/x", VC_AUTH),
    # storage_policy uses the list-with-filter pattern (no per-id GET path),
    # so it's covered by its own dedicated tests rather than this matrix.
    (vcenter_tag, "https://vc.test/api/cis/tagging/tag/x", VC_AUTH),
    (sddc_host, "https://sm.test/v1/hosts/x", SM_AUTH),
    (sddc_cluster, "https://sm.test/v1/clusters/x", SM_AUTH),
    (sddc_domain, "https://sm.test/v1/domains/x", SM_AUTH),
    (nsx_segment, "https://nsx.test/policy/api/v1/infra/segments/x", NX_AUTH),
    (nsx_tier0, "https://nsx.test/policy/api/v1/infra/tier-0s/x", NX_AUTH),
    (nsx_tier1, "https://nsx.test/policy/api/v1/infra/tier-1s/x", NX_AUTH),
    (
        nsx_group,
        "https://nsx.test/policy/api/v1/infra/domains/default/groups/x",
        NX_AUTH,
    ),
    (
        nsx_security_policy,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies/x",
        NX_AUTH,
    ),
    (nsx_service, "https://nsx.test/policy/api/v1/infra/services/x", NX_AUTH),
    (
        nsx_context_profile,
        "https://nsx.test/policy/api/v1/infra/context-profiles/x",
        NX_AUTH,
    ),
    (nsx_transport_zone, "https://nsx.test/api/v1/transport-zones/x", NX_AUTH),
    (nsx_transport_node, "https://nsx.test/api/v1/transport-nodes/x", NX_AUTH),
    (
        nsx_compute_collection,
        "https://nsx.test/api/v1/fabric/compute-collections/x",
        NX_AUTH,
    ),
    (nsx_role_binding, "https://nsx.test/api/v1/aaa/role-bindings/x", NX_AUTH),
    (vcfops_resource, "https://ops.test/suite-api/api/resources/x", OPS_AUTH),
    (vcfops_adapter, "https://ops.test/suite-api/api/adapterkinds/x", OPS_AUTH),
    (vcfops_policy, "https://ops.test/suite-api/api/policies/x", OPS_AUTH),
    (
        vcenter_supervisor_service,
        "https://vc.test/api/vcenter/namespace-management/supervisor-services/x",
        VC_AUTH,
    ),
    (
        vcenter_supervisor_software,
        "https://vc.test/api/vcenter/namespace-management/software/clusters/x",
        VC_AUTH,
    ),
    (
        vcenter_vm_class,
        "https://vc.test/api/vcenter/namespace-management/virtual-machine-classes/x",
        VC_AUTH,
    ),
    (sddc_vcf_services, "https://sm.test/v1/vcf-services/x", SM_AUTH),
    (vcfops_collector, "https://ops.test/suite-api/api/collectors/x", OPS_AUTH),
    (vcfops_credential, "https://ops.test/suite-api/api/credentials/x", OPS_AUTH),
    (
        vcfops_recommendation,
        "https://ops.test/suite-api/api/recommendations/x",
        OPS_AUTH,
    ),
    (
        vcfops_resource_group,
        "https://ops.test/suite-api/api/resources/groups/x",
        OPS_AUTH,
    ),
    (vcfops_supermetric, "https://ops.test/suite-api/api/supermetrics/x", OPS_AUTH),
    (vcfops_report, "https://ops.test/suite-api/api/reports/x", OPS_AUTH),
    (
        vcfops_maintenance,
        "https://ops.test/suite-api/api/maintenanceschedules/x",
        OPS_AUTH,
    ),
    (vcfops_task, "https://ops.test/suite-api/api/tasks/x", OPS_AUTH),
    (vcfops_solution, "https://ops.test/suite-api/api/solutions/x", OPS_AUTH),
]


@pytest.mark.parametrize(
    "mod,url,auth_fixture", CASES, ids=lambda x: getattr(x, "__name__", str(x))
)
def test_get_or_none_returns_none_on_404(request, opts, mod, url, auth_fixture):
    rsps = request.getfixturevalue(auth_fixture)
    rsps.add(responses.GET, url, status=404)
    assert mod.get_or_none(opts, "x") is None


@pytest.mark.parametrize(
    "mod,url,auth_fixture", CASES, ids=lambda x: getattr(x, "__name__", str(x))
)
def test_get_or_none_propagates_500(request, opts, mod, url, auth_fixture):
    rsps = request.getfixturevalue(auth_fixture)
    rsps.add(responses.GET, url, status=500)
    with pytest.raises(requests.HTTPError):
        mod.get_or_none(opts, "x")


# ---------------------------------------------------------------------------
# ESXi clients (SOAP / pyVmomi, not REST). Each ``get_or_none`` returns
# ``None`` when the underlying lookup fails the way "not found" surfaces in
# pyVmomi for that sub-manager, and propagates anything else.
# ---------------------------------------------------------------------------


def test_esxi_firewall_get_or_none_returns_none_when_missing(opts):
    host = MagicMock()
    host.configManager.firewallSystem.firewallInfo.ruleset = []  # no matching ruleset
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert esxi_firewall.get_or_none(opts, "missing") is None


def test_esxi_service_get_or_none_returns_none_when_missing(opts):
    host = MagicMock()
    host.configManager.serviceSystem.serviceInfo.service = []  # no matching service
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert esxi_service.get_or_none(opts, "missing") is None


def test_esxi_advanced_get_or_none_returns_none_when_missing(opts):
    host = MagicMock()
    host.configManager.advancedOption.QueryOptions.return_value = []  # empty result
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert esxi_advanced.get_or_none(opts, "Missing.Key") is None
