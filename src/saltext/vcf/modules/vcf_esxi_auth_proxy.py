"""Execution module for the ESXi vSphere Authentication Proxy (CAM)."""

from saltext.vcf.clients import esxi_auth_proxy as c

__virtualname__ = "vcf_esxi_auth_proxy"


def __virtual__():
    return __virtualname__


def get_config(host, profile=None):
    """Return CAM address, verify flag, and current AD-join state for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_auth_proxy.get_config esxi-01

    """
    return c.get_config(__opts__, host, profile=profile)


def set_config(host, cam_address=None, verify_cam_cert=None, profile=None):
    """Set the CAM advanced settings on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_auth_proxy.set_config esxi-01 cam_address=cam.example.com verify_cam_cert=True

    """
    return c.set_config(
        __opts__,
        host,
        cam_address=cam_address,
        verify_cam_cert=verify_cam_cert,
        profile=profile,
    )


def join_domain_via_cam(host, domain_name, cam_server, profile=None):
    """Join *host* to *domain_name* via CAM (auth proxy) *cam_server*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_auth_proxy.join_domain_via_cam esxi-01 example.com cam.example.com

    """
    return c.join_domain_via_cam(__opts__, host, domain_name, cam_server, profile=profile)


def leave_domain(host, force=False, profile=None):
    """Leave the current AD domain on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_auth_proxy.leave_domain esxi-01 force=True

    """
    return c.leave_domain(__opts__, host, force=force, profile=profile)
