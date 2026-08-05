"""Execution module for vSAN File Service."""

from saltext.vcf.clients import vsan_file_service as c

__virtualname__ = "vcf_vsan_file_service"


def __virtual__():
    return __virtualname__


def enabled(cluster, profile=None):
    """Enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_file_service.enabled <cluster>

    """
    return c.enabled(__opts__, cluster, profile=profile)


def set_enabled(cluster, enabled_, network_name=None, profile=None):
    """Set enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_file_service.set_enabled <cluster> True network_name=VM-Mgmt

    """
    return c.set_enabled(__opts__, cluster, enabled_, network_name=network_name, profile=profile)


def download_ovf(cluster, ovf_url=None, profile=None):
    """Download ovf.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_file_service.download_ovf <cluster>

    """
    return c.download_ovf(__opts__, cluster, ovf_url=ovf_url, profile=profile)


def list_domains(cluster, profile=None):
    """List domains.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_file_service.list_domains <cluster>

    """
    return c.list_domains(__opts__, cluster, profile=profile)


def create_domain(
    cluster,
    domain_name,
    ip_to_fqdn,
    subnet_mask,
    gateway_address,
    dns_suffixes,
    dns_address,
    profile=None,
):
    """Create domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_file_service.create_domain <cluster> fileshare '{"10.0.0.1": "f0.test"}' 255.255.255.0 10.0.0.250 '["test"]' '["10.0.0.250"]'

    """
    return c.create_domain(
        __opts__,
        cluster,
        domain_name,
        ip_to_fqdn,
        subnet_mask,
        gateway_address,
        dns_suffixes,
        dns_address,
        profile=profile,
    )


def remove_domain(cluster, domain_name, profile=None):
    """Remove domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_file_service.remove_domain <cluster> fileshare

    """
    return c.remove_domain(__opts__, cluster, domain_name, profile=profile)
