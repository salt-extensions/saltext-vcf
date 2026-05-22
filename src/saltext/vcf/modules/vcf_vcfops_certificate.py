"""Execution module for VCF Operations truststore certificates."""

from saltext.vcf.clients import vcfops_certificate as c

__virtualname__ = "vcf_vcfops_certificate"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List every certificate in the VCF Operations truststore.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_certificate.list_
    """
    return c.list_(__opts__, profile=profile)


def get(thumbprint, profile=None):
    """Return the certificate matching *thumbprint*; raises ``KeyError`` if missing.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_certificate.get <thumbprint>
    """
    return c.get(__opts__, thumbprint, profile=profile)


def get_or_none(thumbprint, profile=None):
    """Like :func:`get` but returns ``None`` when no match.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_certificate.get_or_none <thumbprint>
    """
    return c.get_or_none(__opts__, thumbprint, profile=profile)


def delete(thumbprint, force=False, profile=None):
    """Delete a certificate by thumbprint.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_certificate.delete <thumbprint>
    """
    return c.delete(__opts__, thumbprint, force=force, profile=profile)
