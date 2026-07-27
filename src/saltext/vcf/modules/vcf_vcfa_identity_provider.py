"""Execution module for VCF Automation identity-provider registration.

Wraps :mod:`saltext.vcf.clients.vcfa_identity_provider` so operators
can list, register, or delete AD/LDAP/SAML/OIDC identity providers on
an org.

CLI Example:

.. code-block:: bash

    salt '*' vcf_vcfa_identity_provider.list org-1
    salt '*' vcf_vcfa_identity_provider.create org-1 '{"name":"corp-ad","type":"AD",...}'
    salt '*' vcf_vcfa_identity_provider.delete org-1 idp-xyz
"""

from saltext.vcf.clients import vcfa_identity_provider as c

__virtualname__ = "vcf_vcfa_identity_provider"


def __virtual__():
    return __virtualname__


def list_(org_id, profile=None):
    """List IdPs registered against *org_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_identity_provider.list org-1
    """
    return c.identity_provider_list(__opts__, org_id, profile=profile)


def get(org_id, idp_id, profile=None):
    """Fetch a single IdP by id."""
    return c.identity_provider_get(__opts__, org_id, idp_id, profile=profile)


def get_or_none(org_id, idp_id, profile=None):
    """Fetch a single IdP by id; return ``None`` on 404."""
    return c.identity_provider_get_or_none(__opts__, org_id, idp_id, profile=profile)


def find_by_name(org_id, name, profile=None):
    """Return the IdP whose ``name`` matches *name*, or ``None``."""
    return c.find_by_name(__opts__, org_id, name, profile=profile)


def create(org_id, spec, profile=None):
    """Register a new IdP under *org_id*.

    *spec* is a dict passed through as the request body (must include
    ``name`` and ``type`` plus type-specific fields).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_identity_provider.create org-1 '{"name":"corp-ad","type":"AD","url":"ldaps://ad.example.com","baseDn":"..."}'
    """
    return c.identity_provider_create(__opts__, org_id, spec, profile=profile)


def update(org_id, idp_id, spec, profile=None):
    """Replace an existing IdP registration."""
    return c.identity_provider_update(__opts__, org_id, idp_id, spec, profile=profile)


def delete(org_id, idp_id, profile=None):
    """Delete an IdP registration by id."""
    return c.identity_provider_delete(__opts__, org_id, idp_id, profile=profile)
