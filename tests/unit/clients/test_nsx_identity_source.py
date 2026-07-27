"""Tests for the NSX identity-source client (``saltext.vcf.clients.nsx_identity_source``)."""

import pytest
import requests
import responses

from saltext.vcf.clients import nsx_identity_source

BASE = "https://nsx.test/api/v1/aaa/ldap-identity-sources"


def test_list_returns_results(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        BASE,
        json={"results": [{"id": "id-1", "name": "corp-ad"}]},
        status=200,
    )
    result = nsx_identity_source.list_(opts)
    assert result["results"][0]["id"] == "id-1"


def test_get_returns_source(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/id-1",
        json={"id": "id-1", "name": "corp-ad"},
        status=200,
    )
    assert nsx_identity_source.get(opts, "id-1")["name"] == "corp-ad"


def test_get_or_none_returns_source(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/id-1",
        json={"id": "id-1"},
        status=200,
    )
    assert nsx_identity_source.get_or_none(opts, "id-1") == {"id": "id-1"}


def test_get_or_none_returns_none_on_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/missing",
        json={"error_message": "not found"},
        status=404,
    )
    assert nsx_identity_source.get_or_none(opts, "missing") is None


def test_get_or_none_reraises_non_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/boom",
        json={"error_message": "server error"},
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        nsx_identity_source.get_or_none(opts, "boom")


def test_create_posts_body(opts, mocked_responses):
    body = {
        "name": "corp-ad",
        "domain_name": "corp.example.com",
        "type": "ActiveDirectoryOverLdap",
        "base_dn": "DC=corp,DC=example,DC=com",
        "ldap_servers": [{"url": "ldaps://ad1.corp:636"}],
        "bind_identity": "svc-nsx@corp",
        "password": "secret",
        "user_search_filter": "(sAMAccountName=%s)",
    }
    mocked_responses.add(
        responses.POST,
        BASE,
        json={"id": "id-1", **body},
        status=200,
        match=[responses.matchers.json_params_matcher(body)],
    )
    assert nsx_identity_source.create(opts, body)["id"] == "id-1"


def test_update_puts_body(opts, mocked_responses):
    body = {"id": "id-1", "name": "corp-ad", "base_dn": "DC=corp,DC=example,DC=com"}
    mocked_responses.add(
        responses.PUT,
        f"{BASE}/id-1",
        json=body,
        status=200,
        match=[responses.matchers.json_params_matcher(body)],
    )
    assert nsx_identity_source.update(opts, "id-1", body)["base_dn"] == "DC=corp,DC=example,DC=com"


def test_delete_calls_delete(opts, mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        f"{BASE}/id-1",
        status=200,
    )
    assert nsx_identity_source.delete(opts, "id-1") == {}
