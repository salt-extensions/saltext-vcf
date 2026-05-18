"""Execution module for guest OS customization (SOAP)."""

from saltext.vcf.clients import vim_vm_customization as c

__virtualname__ = "vcf_vim_vm_customization"


def __virtual__():
    return __virtualname__


def linux_spec(
    hostname,
    domain,
    time_zone="UTC",
    hw_clock_utc=True,
    nics=None,
    dns_servers=None,
    dns_search_path=None,
):
    """Build a Linux customization spec (returns the pyVmomi object).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_customization.linux_spec web-01 example.com nics='[{"dhcp": true}]'
    """
    return c.linux_spec(
        hostname,
        domain,
        time_zone=time_zone,
        hw_clock_utc=hw_clock_utc,
        nics=nics,
        dns_servers=dns_servers,
        dns_search_path=dns_search_path,
    )


def windows_spec(
    hostname,
    workgroup_or_domain,
    domain_join=False,
    domain_admin=None,
    domain_admin_password=None,
    admin_password=None,
    auto_logon=False,
    auto_logon_count=1,
    license_mode="perServer",
    product_id=None,
    full_name="Administrator",
    org_name="VMware",
    time_zone=85,
    nics=None,
    dns_servers=None,
    dns_search_path=None,
):
    """Build a Windows customization spec.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_customization.windows_spec WIN-01 WORKGROUP admin_password='<pw>'
    """
    return c.windows_spec(
        hostname,
        workgroup_or_domain,
        domain_join=domain_join,
        domain_admin=domain_admin,
        domain_admin_password=domain_admin_password,
        admin_password=admin_password,
        auto_logon=auto_logon,
        auto_logon_count=auto_logon_count,
        license_mode=license_mode,
        product_id=product_id,
        full_name=full_name,
        org_name=org_name,
        time_zone=time_zone,
        nics=nics,
        dns_servers=dns_servers,
        dns_search_path=dns_search_path,
    )


def apply(vm, spec, profile=None):
    """Apply a customization spec to an existing VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_customization.apply vm-100 <spec>
    """
    return c.apply(__opts__, vm, spec, profile=profile)


def spec_list(profile=None):
    """List saved customization specs on the vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_customization.spec_list
    """
    return c.spec_list(__opts__, profile=profile)


def spec_delete(name, profile=None):
    """Delete a saved customization spec by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_customization.spec_delete linux-prod
    """
    return c.spec_delete(__opts__, name, profile=profile)
