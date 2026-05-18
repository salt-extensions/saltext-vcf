"""Tests for SDDC-mediated VMSP services client."""

import responses

from saltext.vcf.clients import sddc_vcf_services

SAMPLE = {
    "elements": [
        {"id": "u-1", "name": "COMMON_SERVICES", "version": "9.2.0", "status": "UP"},
        {"id": "u-2", "name": "DOMAIN_MANAGER", "version": "9.2.0", "status": "UP"},
        {"id": "u-3", "name": "LCM", "version": "9.2.0", "status": "UP"},
    ]
}


def test_list_and_get(opts, sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/vcf-services", json=SAMPLE, status=200)
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/vcf-services/u-1",
        json=SAMPLE["elements"][0],
        status=200,
    )
    assert sddc_vcf_services.list_(opts) == SAMPLE
    assert sddc_vcf_services.get(opts, "u-1")["name"] == "COMMON_SERVICES"


def test_get_or_none(opts, sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/vcf-services/missing", status=404)
    assert sddc_vcf_services.get_or_none(opts, "missing") is None


def test_get_by_name(opts, sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/vcf-services", json=SAMPLE, status=200)
    assert sddc_vcf_services.get_by_name(opts, "DOMAIN_MANAGER")["id"] == "u-2"


def test_get_by_name_missing(opts, sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/vcf-services", json=SAMPLE, status=200)
    assert sddc_vcf_services.get_by_name(opts, "NOPE") is None


def test_get_by_name_empty(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/vcf-services",
        json={"elements": []},
        status=200,
    )
    assert sddc_vcf_services.get_by_name(opts, "X") is None
