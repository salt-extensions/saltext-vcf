"""NSX Policy API LDAP identity sources.

Sources use caller-supplied IDs and PUT requests at
``/policy/api/v1/aaa/ldap-identity-sources/{source-id}``.
"""

from urllib.parse import quote

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/aaa/ldap-identity-sources"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def create(opts, name, ldap_servers, base_dn, profile=None, **spec):
    """Create a source using *name* as its ID and display name.

    Requires resource_type (ActiveDirectoryIdentitySource or
    OpenLdapIdentitySource) and domain_name in spec. Additional directory
    options pass through to the API.
    """
    if spec.get("resource_type") not in (
        "ActiveDirectoryIdentitySource", "OpenLdapIdentitySource"
    ):
        raise ValueError(
            "resource_type must be ActiveDirectoryIdentitySource or OpenLdapIdentitySource"
        )
    domain = spec.get("domain_name")
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain_name is required")
    if not isinstance(ldap_servers, (list, tuple)):
        raise ValueError("ldap_servers must be a list of LDAP server configurations")
    body = dict(spec)
    body.update({
        "id": name,
        "display_name": name,
        "ldap_servers": list(ldap_servers),
        "base_dn": base_dn,
    })
    return nsx.api_put(opts, f"{PATH}/{quote(name, safe='')}", body=body, profile=profile)


def update(opts, source_id, body, profile=None):
    return nsx.api_put(opts, f"{PATH}/{quote(source_id, safe='')}", body=body, profile=profile)


def delete(opts, source_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{quote(source_id, safe='')}", profile=profile)
