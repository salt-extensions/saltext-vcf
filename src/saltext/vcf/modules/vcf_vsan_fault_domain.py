"""Execution module for vSAN fault-domain management (SOAP)."""

from saltext.vcf.clients import vsan_fault_domain as c

__virtualname__ = "vcf_vsan_fault_domain"


def __virtual__():
    return __virtualname__


def list_(cluster, profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_fault_domain.list_ <cluster>

    """
    return c.list_(__opts__, cluster, profile=profile)


def assign(cluster, mapping, profile=None):
    """Assign.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_fault_domain.assign <cluster> <mapping>

    """
    return c.assign(__opts__, cluster, mapping, profile=profile)
