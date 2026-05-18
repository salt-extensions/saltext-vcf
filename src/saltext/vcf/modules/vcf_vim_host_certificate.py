"""Execution module for ESXi host SSL certificate management."""

from saltext.vcf.clients import vim_host_certificate as c

__virtualname__ = "vcf_vim_host_certificate"


def __virtual__():
    return __virtualname__


def info(host, profile=None):
    """Return host cert info: issuer/subject/not_before/not_after/pem.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_certificate.info <host>
    """
    return c.info(__opts__, host, profile=profile)


def generate_csr(host, useip=True, profile=None):
    """Generate a CSR for *host*. Returns PEM-encoded CSR.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_certificate.generate_csr <host>
    """
    return c.generate_csr(__opts__, host, useip=useip, profile=profile)


def install_cert(host, cert_pem, profile=None):
    """Install a signed cert PEM on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_certificate.install_cert <host> <cert_pem>
    """
    return c.install_cert(__opts__, host, cert_pem, profile=profile)


def refresh_cert(host, profile=None):
    """Re-fetch the host cert from VECS / KMS.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_certificate.refresh_cert <host>
    """
    return c.refresh_cert(__opts__, host, profile=profile)


def refresh_ca_bundle(host, profile=None):
    """Refresh the trusted CA bundle on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_certificate.refresh_ca_bundle <host>
    """
    return c.refresh_ca_bundle(__opts__, host, profile=profile)
