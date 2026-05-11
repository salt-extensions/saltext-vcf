"""SDDC Manager domain-scoped certificate management."""

import requests

from saltext.vmware.utils import sddc


def _base(domain_id):
    return f"/v1/domains/{domain_id}"


def list_(opts, domain_id, profile=None):
    """List installed certificates on resources in the domain."""
    return sddc.api_get(opts, f"{_base(domain_id)}/certificates", profile=profile)


def list_csrs(opts, domain_id, profile=None):
    return sddc.api_get(opts, f"{_base(domain_id)}/csrs", profile=profile)


def create_csrs(opts, domain_id, csr_specs, profile=None):
    """Generate CSRs for resources in the domain.

    *csr_specs* is a list per the SDDC Manager API — e.g. ``[{"resourceType":
    "VCENTER", "country": "US", ...}]``.
    """
    return sddc.api_put(opts, f"{_base(domain_id)}/csrs", body=csr_specs, profile=profile)


def install_certificates(opts, domain_id, cert_specs, profile=None):
    """Install certificates for domain resources."""
    return sddc.api_patch(
        opts, f"{_base(domain_id)}/certificates", body=cert_specs, profile=profile
    )


def get_or_none(opts, domain_id, profile=None):
    try:
        return list_(opts, domain_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
