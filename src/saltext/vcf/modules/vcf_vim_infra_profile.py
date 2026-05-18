"""Execution module for vSphere host profiles."""

from saltext.vcf.clients import vim_infra_profile as c

__virtualname__ = "vcf_vim_infra_profile"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List host profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_infra_profile.list_
    """
    return c.list_(__opts__, profile=profile)


def get(host_profile, profile=None):
    """Return one host profile by id or name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_infra_profile.get <host_profile>
    """
    return c.get(__opts__, host_profile, profile=profile)


def export(host_profile, profile=None):
    """Return the profile's XML export.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_infra_profile.export <host_profile>
    """
    return c.export(__opts__, host_profile, profile=profile)


def check_compliance(host_profile, profile=None):
    """Trigger a compliance check.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_infra_profile.check_compliance <host_profile>
    """
    return c.check_compliance(__opts__, host_profile, profile=profile)
