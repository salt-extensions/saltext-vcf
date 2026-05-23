"""Tests for the IaaS-rooted vcfa_* clients."""

import json

import responses

from saltext.vcf.clients import vcfa_cloud_account
from saltext.vcf.clients import vcfa_cloud_zone
from saltext.vcf.clients import vcfa_network_profile
from saltext.vcf.clients import vcfa_storage_profile

# -- cloud_account ---------------------------------------------------------


def test_cloud_account_list_unwraps_content(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/iaas/api/cloud-accounts",
        json={"content": [{"id": "ca-1"}, {"id": "ca-2"}]},
        status=200,
    )
    assert [a["id"] for a in vcfa_cloud_account.list_(opts)] == ["ca-1", "ca-2"]


def test_cloud_account_get_or_none_returns_none_on_404(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, "https://vcfa.test/iaas/api/cloud-accounts/missing", status=404)
    assert vcfa_cloud_account.get_or_none(opts, "missing") is None


def test_cloud_account_create_vsphere_targets_provider_path(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/cloud-accounts-vsphere",
        json={"id": "ca-1"},
        status=200,
    )
    vcfa_cloud_account.create_vsphere(opts, {"name": "vc-prod"})
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"name": "vc-prod"}


def test_cloud_account_create_nsxt_targets_provider_path(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/cloud-accounts-nsx-t",
        json={"id": "ca-2"},
        status=200,
    )
    vcfa_cloud_account.create_nsxt(opts, {"name": "nsx-prod"})


def test_cloud_account_regions(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/iaas/api/cloud-accounts/ca-1/regions",
        json={"content": [{"id": "r-1"}]},
        status=200,
    )
    assert vcfa_cloud_account.regions(opts, "ca-1") == {"content": [{"id": "r-1"}]}


# -- cloud_zone -----------------------------------------------------------


def test_zone_list(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/iaas/api/zones",
        json={"content": [{"id": "z-1"}]},
        status=200,
    )
    assert vcfa_cloud_zone.list_(opts) == [{"id": "z-1"}]


def test_zone_create_sends_body(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/zones",
        json={"id": "z-1"},
        status=200,
    )
    vcfa_cloud_zone.create(opts, {"name": "z-prod", "regionId": "r-1"})
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"name": "z-prod", "regionId": "r-1"}


def test_zone_delete(opts, vcfa_authed):
    vcfa_authed.add(responses.DELETE, "https://vcfa.test/iaas/api/zones/z-1", status=204)
    assert vcfa_cloud_zone.delete(opts, "z-1") == {}


# -- storage_profile -----------------------------------------------------


def test_storage_profile_create_vsphere(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/storage-profiles-vsphere",
        json={"id": "sp-1"},
        status=200,
    )
    vcfa_storage_profile.create_vsphere(opts, {"name": "sp-prod"})


def test_storage_profile_delete_uses_generic_path(opts, vcfa_authed):
    vcfa_authed.add(
        responses.DELETE, "https://vcfa.test/iaas/api/storage-profiles/sp-1", status=204
    )
    assert vcfa_storage_profile.delete(opts, "sp-1") == {}


# -- network_profile ----------------------------------------------------


def test_network_profile_create(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/network-profiles",
        json={"id": "np-1"},
        status=200,
    )
    vcfa_network_profile.create(opts, {"name": "np-prod", "regionId": "r-1"})


def test_network_profile_update_is_patch(opts, vcfa_authed):
    vcfa_authed.add(
        responses.PATCH,
        "https://vcfa.test/iaas/api/network-profiles/np-1",
        json={"id": "np-1"},
        status=200,
    )
    vcfa_network_profile.update(opts, "np-1", {"description": "updated"})
