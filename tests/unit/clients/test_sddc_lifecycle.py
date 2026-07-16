"""Tests for the Batch 6 SDDC Manager lifecycle clients."""

import json

import responses

from saltext.vcf.clients import sddc_bundles
from saltext.vcf.clients import sddc_certificates
from saltext.vcf.clients import sddc_manager
from saltext.vcf.clients import sddc_network_pools
from saltext.vcf.clients import sddc_personalities
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


# ---------- async-patch building blocks ----------


def test_bundles_upload_posts_upload_spec(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        "https://sm.test/v1/bundles",
        json={"id": "task-upload"},
        status=200,
    )
    sddc_bundles.upload(
        opts,
        bundle_file_path="/nfs/.../b.tar",
        manifest_file_path="/nfs/.../b.manifest",
        signature_file_path="/nfs/.../b.sig",
    )
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body["bundleUploadSpec"] == {
        "bundleFilePath": "/nfs/.../b.tar",
        "manifestFilePath": "/nfs/.../b.manifest",
        "signatureFilePath": "/nfs/.../b.sig",
    }


def test_bundles_delete_uses_delete(opts, sddc_authed):
    sddc_authed.add(
        responses.DELETE,
        "https://sm.test/v1/bundles/b1",
        status=204,
    )
    sddc_bundles.delete(opts, "b1")
    assert sddc_authed.calls[-1].request.method == "DELETE"


def test_bundles_for_skip_upgrade(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/bundles/domains/d1",
        json={"elements": []},
        status=200,
    )
    assert sddc_bundles.for_skip_upgrade(opts, "d1") == {"elements": []}


def test_releases_custom_patches(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/releases/domains/d1/custom-patches",
        json={"elements": []},
        status=200,
    )
    sddc_releases.custom_patches(opts, "d1")
    assert sddc_authed.calls[-1].request.url.endswith("/v1/releases/domains/d1/custom-patches")


def test_personalities_list_no_filter(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/personalities",
        json={"elements": []},
        status=200,
    )
    sddc_personalities.list_(opts)
    # No query string when no filters supplied.
    assert "?" not in sddc_authed.calls[-1].request.url


def test_personalities_list_filters(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/personalities",
        json={"elements": []},
        status=200,
    )
    sddc_personalities.list_(opts, personality_name="img-8u3", cluster_id="c1")
    url = sddc_authed.calls[-1].request.url
    assert "personalityName=img-8u3" in url
    assert "clusterId=c1" in url


def test_personalities_get_or_none_404(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/personalities/p-missing",
        json={"message": "not found"},
        status=404,
    )
    assert sddc_personalities.get_or_none(opts, "p-missing") is None


def test_personalities_create_posts_spec(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        "https://sm.test/v1/personalities",
        json={"id": "p1"},
        status=200,
    )
    sddc_personalities.create(opts, {"personalityName": "img", "fileId": "f1"})
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body["personalityName"] == "img"


def test_personalities_delete_uses_delete(opts, sddc_authed):
    sddc_authed.add(
        responses.DELETE,
        "https://sm.test/v1/personalities/p1",
        status=204,
    )
    sddc_personalities.delete(opts, "p1")
    assert sddc_authed.calls[-1].request.method == "DELETE"


def test_personalities_rename_uses_patch(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        "https://sm.test/v1/personalities/p1",
        json={},
        status=200,
    )
    sddc_personalities.rename(opts, "p1", "img-new")
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"personalityName": "img-new"}


def test_personalities_upload_files_uses_put(opts, sddc_authed):
    sddc_authed.add(
        responses.PUT,
        "https://sm.test/v1/personalities/files",
        json={"id": "file-1"},
        status=200,
    )
    sddc_personalities.upload_files(opts, {"filePath": "/nfs/p.zip"})
    assert sddc_authed.calls[-1].request.method == "PUT"
