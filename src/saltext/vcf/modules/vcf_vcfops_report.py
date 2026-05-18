"""Execution module for VCF Operations report instances."""

from saltext.vcf.clients import vcfops_report as c

__virtualname__ = "vcf_vcfops_report"


def __virtual__():
    return __virtualname__


def list_(page=0, page_size=1000):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_report.list_ <page> <page_size>

    """
    return c.list_(__opts__, page=page, page_size=page_size)


def get(report_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_report.get <report_id>

    """
    return c.get(__opts__, report_id)


def generate(report_spec):
    """Generate.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_report.generate <report_spec>

    """
    return c.generate(__opts__, report_spec)


def download(report_id, fmt="PDF"):
    """Download.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_report.download <report_id> <fmt>

    """
    return c.download(__opts__, report_id, fmt=fmt)


def delete(report_id):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_report.delete <report_id>

    """
    return c.delete(__opts__, report_id)
