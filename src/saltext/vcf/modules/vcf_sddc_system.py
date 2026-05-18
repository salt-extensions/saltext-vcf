"""Execution module for SDDC Manager system info, users, roles, personalities, AVNs."""

from saltext.vcf.clients import sddc_avn as avn
from saltext.vcf.clients import sddc_system as system
from saltext.vcf.clients import sddc_users as users

__virtualname__ = "vcf_sddc_system"


def __virtual__():
    return __virtualname__


def system_info(profile=None):
    """Return SDDC Manager system info.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.system_info
    """
    return system.get_system(__opts__, profile=profile)


def list_personalities(profile=None):
    """List installed vSphere Lifecycle Manager personalities (images).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.list_personalities
    """
    return system.list_personalities(__opts__, profile=profile)


def get_personality(personality_id, profile=None):
    """Return one personality.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.get_personality <personality-id>
    """
    return system.get_personality(__opts__, personality_id, profile=profile)


def list_users(profile=None):
    """List SDDC Manager users.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.list_users
    """
    return users.list_users(__opts__, profile=profile)


def list_roles(profile=None):
    """List SDDC Manager roles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.list_roles
    """
    return users.list_roles(__opts__, profile=profile)


def add_users(user_specs, profile=None):
    """Bulk-add SDDC Manager users.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.add_users '[{...}]'
    """
    return users.add_users(__opts__, user_specs, profile=profile)


def delete_user(user_id, profile=None):
    """Delete an SDDC Manager user.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.delete_user <user-id>
    """
    return users.delete_user(__opts__, user_id, profile=profile)


def list_avns(profile=None):
    """List Application Virtual Networks.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_system.list_avns
    """
    return avn.list_(__opts__, profile=profile)
