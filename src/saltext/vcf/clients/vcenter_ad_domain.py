"""Client for vCenter Server's AD domain join (Active Directory identity provider).

Thin wrapper around :mod:`vcenter_sso`'s identity-provider endpoints, scoped
to the ``ActiveDirectory`` ``config_tag`` — the vSphere REST equivalent of
joining the vCenter Server's SSO domain to Active Directory.
"""

from saltext.vcf.clients import vcenter_sso as sso_c


def get(opts, domain_name, profile=None):
    """Return the AD identity provider joined to *domain_name*, or ``None``."""
    for provider in sso_c.providers_list(opts, profile=profile) or []:
        if (
            provider.get("config_tag") == "ActiveDirectory"
            and provider.get("domain_name") == domain_name
        ):
            return provider
    return None


def join(opts, domain_name, username, password, profile=None):
    """Join the vCenter Server to *domain_name* as an Active Directory identity provider.

    Returns the new provider id.
    """
    spec = {
        "config_tag": "ActiveDirectory",
        "domain_name": domain_name,
        "username": username,
        "password": password,
    }
    return sso_c.providers_create(opts, spec, profile=profile)


def leave(opts, provider_id, profile=None):
    """Remove the AD identity provider, leaving the domain."""
    return sso_c.providers_delete(opts, provider_id, profile=profile)
