"""NSX Manager LDAP/AD identity sources (``/api/v1/aaa/ldap-identity-sources``).

An identity source federates NSX Manager RBAC against Active Directory or
another LDAP so operator privileges are managed centrally in AD rather than
via local NSX accounts. Pair with :mod:`saltext.vcf.clients.nsx_role_binding`
to grant AD principals scoped roles.
"""

import requests

from saltext.vcf.utils import nsx

PATH = "/api/v1/aaa/ldap-identity-sources"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, source_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{source_id}", profile=profile)


def get_or_none(opts, source_id, profile=None):
    try:
        return get(opts, source_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, body, profile=None):
    """POST a new LDAP identity source. *body* matches the NSX schema.

    Typical body::

        {
            "name": "corp-ad",
            "domain_name": "corp.example.com",
            "type": "ActiveDirectoryOverLdap",
            "base_dn": "DC=corp,DC=example,DC=com",
            "ldap_servers": [
                {"url": "ldaps://ad1.corp:636", "certificates": ["-----BEGIN CERT..."]}
            ],
            "bind_identity": "svc-nsx@corp",
            "password": "...",
            "user_search_filter": "(sAMAccountName=%s)"
        }
    """
    return nsx.api_post(opts, PATH, body=body, profile=profile)


def update(opts, source_id, body, profile=None):
    """PUT to update an identity source. NSX Manager AAA uses PUT for update."""
    return nsx.api_put(opts, f"{PATH}/{source_id}", body=body, profile=profile)


def delete(opts, source_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{source_id}", profile=profile)
