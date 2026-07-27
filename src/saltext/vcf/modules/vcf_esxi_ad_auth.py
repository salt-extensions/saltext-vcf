"""Execution module for ESXi native Active Directory join.

Covers 912-controls ``ESXi.enable-ad-auth_adv``: join an ESXi host to an
AD domain natively (plaintext AD credentials sent to the host).  For the
CAM/auth-proxy variant see ``vcf_esxi_auth_proxy``.
"""

from saltext.vcf.clients import esxi_ad_auth as c

__virtualname__ = "vcf_esxi_ad_auth"


def __virtual__():
    return __virtualname__


def get_ad_state(host, profile=None):
    """Return the current AD-join state for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_ad_auth.get_ad_state esxi-01

    """
    return c.get_ad_state(__opts__, host, profile=profile)


def join_domain(host, domain_name, username, password, profile=None):
    """Join *host* to *domain_name* using AD *username* / *password*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_ad_auth.join_domain esxi-01 corp.example.com \\
            'CORP\\svc-esx-join' 'S3cret!'

    """
    return c.join_domain(__opts__, host, domain_name, username, password, profile=profile)


def leave_domain(host, force=False, profile=None):
    """Leave the current AD domain on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_ad_auth.leave_domain esxi-01 force=True

    """
    return c.leave_domain(__opts__, host, force=force, profile=profile)
