"""Tests for clients.vcenter_datacenter (name lookup + folder resolution)."""

import pytest
import responses

from saltext.vcf.clients import vcenter_datacenter


def test_get_by_name_found(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datacenter",
        json=[{"datacenter": "datacenter-42", "name": "DC1"}],
        status=200,
    )
    result = vcenter_datacenter.get_by_name(opts, "DC1")
    assert result == {"datacenter": "datacenter-42", "name": "DC1"}


def test_get_by_name_missing(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datacenter",
        json=[],
        status=200,
    )
    assert vcenter_datacenter.get_by_name(opts, "MISSING") is None


def test_create_resolves_default_folder(opts, vcenter_authed):
    # No folder supplied -> client must look up a DATACENTER-type folder first.
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/folder",
        json=[{"folder": "group-d1", "name": "Datacenters"}],
        status=200,
    )
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/datacenter",
        json="datacenter-99",
        status=200,
    )
    assert vcenter_datacenter.create(opts, "NewDC") == "datacenter-99"
    post_call = [c for c in vcenter_authed.calls if c.request.method == "POST"][-1]
    assert b'"folder": "group-d1"' in post_call.request.body
    assert b'"name": "NewDC"' in post_call.request.body


def test_create_no_folder_available_raises(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/folder",
        json=[],
        status=200,
    )
    with pytest.raises(ValueError):
        vcenter_datacenter.create(opts, "NewDC")


def test_create_keeps_explicit_folder(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/datacenter",
        json="datacenter-7",
        status=200,
    )
    assert vcenter_datacenter.create(opts, "DC1", folder="folder-1") == "datacenter-7"
    post_call = [c for c in vcenter_authed.calls if c.request.method == "POST"][-1]
    assert b'"folder": "folder-1"' in post_call.request.body


def test_api_error_surfaces_body(opts, vcenter_authed):
    import requests

    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/datacenter",
        json={"messages": [{"default_message": "folder is required"}]},
        status=400,
    )
    with pytest.raises(requests.HTTPError) as exc:
        vcenter_datacenter.create(opts, "DC1", folder="folder-1")
    assert "folder is required" in str(exc.value)
