"""LDAP Policy API request regression tests."""

from unittest.mock import patch

import pytest

from saltext.vcf.clients import nsx_ldap as c


@pytest.mark.parametrize("resource_type", [
    "ActiveDirectoryIdentitySource", "OpenLdapIdentitySource",
])
def test_create_uses_named_put(resource_type):
    servers = [{"url": "ldaps://ldap.example.test:636", "bind_identity": "test"}]
    with patch.object(c.nsx, "api_put", return_value={}) as put:
        c.create({}, "corp ldap", servers, "dc=example,dc=test", profile="lab",
                 resource_type=resource_type, domain_name="example.test")
    put.assert_called_once_with(
        {}, c.PATH + "/corp%20ldap", profile="lab", body={
            "id": "corp ldap", "display_name": "corp ldap",
            "resource_type": resource_type, "domain_name": "example.test",
            "base_dn": "dc=example,dc=test", "ldap_servers": servers,
        },
    )


@pytest.mark.parametrize("spec", [
    {}, {"resource_type": "invalid", "domain_name": "example.test"},
    {"resource_type": "ActiveDirectoryIdentitySource"},
    {"resource_type": "ActiveDirectoryIdentitySource", "domain_name": " "},
])
def test_missing_or_invalid_directory_fields_do_not_write(spec):
    with patch.object(c.nsx, "api_put") as put:
        with pytest.raises(ValueError):
            c.create({}, "corp", [], "dc=example,dc=test", **spec)
        put.assert_not_called()


def test_list_and_delete_use_policy_path():
    with patch.object(c.nsx, "api_get", return_value={"results": []}) as get:
        assert c.list_({}, profile="lab") == {"results": []}
        get.assert_called_once_with({}, c.PATH, profile="lab")
    with patch.object(c.nsx, "api_delete") as delete:
        c.delete({}, "corp ldap", profile="lab")
        delete.assert_called_once_with({}, c.PATH + "/corp%20ldap", profile="lab")
