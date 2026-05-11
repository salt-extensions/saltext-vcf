"""Execution module for SDDC Manager-mediated VMSP services (``/v1/vcf-services``)."""

from saltext.vmware.clients import sddc_vcf_services as c

__virtualname__ = "vmware_vcf_services"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcf_services.list_

    """
    return c.list_(__opts__, profile=profile)


def get(service_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcf_services.get <service_id>

    """
    return c.get(__opts__, service_id, profile=profile)


def get_by_name(name, profile=None):
    """Get by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcf_services.get_by_name <name>

    """
    return c.get_by_name(__opts__, name, profile=profile)


def status_map(profile=None):
    """Return a ``{name: status}`` summary across all VMSP services.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcf_services.status_map

    """
    body = c.list_(__opts__, profile=profile)
    elements = body.get("elements") if isinstance(body, dict) else None
    if not elements:
        return {}
    return {element["name"]: element.get("status") for element in elements}


def healthy(profile=None):
    """Return ``True`` when every VMSP service reports ``UP``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcf_services.healthy

    """
    return all(status == "UP" for status in status_map(profile=profile).values())
