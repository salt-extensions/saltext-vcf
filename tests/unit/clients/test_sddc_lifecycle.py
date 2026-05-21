"""Tests for the Batch 6 SDDC Manager lifecycle clients."""

import json

import responses

from saltext.vcf.clients import sddc_bundles
from saltext.vcf.clients import sddc_certificates
from saltext.vcf.clients import sddc_manager
from saltext.vcf.clients import sddc_network_pools
from saltext.vcf.clients import sddc_releases
from saltext.vcf.clients import sddc_upgrades
from saltext.vcf.clients import sddc_vcenters


def test_vcenters_list(opts, sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/vcenters", json={"elements": []}, status=200)
    assert sddc_vcenters.list_(opts) == {"elements": []}


def test_bundles_download_triggers_patch(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        "https://sm.test/v1/bundles/b1",
        json={"id": "task-1"},
        status=200,
    )
    sddc_bundles.download(opts, "b1")


def test_network_pool_create_post(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        "https://sm.test/v1/network-pools",
        json={"id": "np1"},
        status=200,
    )
    sddc_network_pools.create(opts, {"name": "Pool1"})


def test_releases_filter_by_domain(opts, sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/releases", json={"elements": []}, status=200)
    sddc_releases.domain(opts, "domain-1")
    assert "domainId=domain-1" in sddc_authed.calls[-1].request.url


def test_releases_system(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/system/release",
        json={"version": "9.2"},
        status=200,
    )
    assert sddc_releases.system(opts) == {"version": "9.2"}


def test_upgrade_start_post(opts, sddc_authed):
    sddc_authed.add(responses.POST, "https://sm.test/v1/upgrades", json={"id": "u1"}, status=200)
    sddc_upgrades.start(opts, {"bundleId": "b1"})


def test_manager_get(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/sddc-manager",
        json={"version": "9.2"},
        status=200,
    )
    assert sddc_manager.get(opts) == {"version": "9.2"}


def test_certificates_csr_uses_put(opts, sddc_authed):
    sddc_authed.add(
        responses.PUT,
        "https://sm.test/v1/domains/d1/csrs",
        json={"elements": []},
        status=200,
    )
    sddc_certificates.create_csrs(
        opts,
        "d1",
        csr_generation_spec={"keyAlgorithm": "RSA", "keySize": "2048"},
        resources=[{"type": "VCENTER", "fqdn": "vc.test"}],
    )
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body["csrGenerationSpec"]["keyAlgorithm"] == "RSA"
    assert body["resources"][0]["type"] == "VCENTER"
