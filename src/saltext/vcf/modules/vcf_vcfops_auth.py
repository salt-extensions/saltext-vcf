"""Execution module for VCF Operations identity (auth sources/roles/users/groups)."""

from saltext.vcf.clients import vcfops_auth as c

__virtualname__ = "vcf_vcfops_auth"


def __virtual__():
    return __virtualname__


def sources_list(profile=None):
    """Sources list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.sources_list

    """
    return c.sources_list(__opts__, profile=profile)


def sources_get(source_id, profile=None):
    """Sources get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.sources_get <source_id>

    """
    return c.sources_get(__opts__, source_id, profile=profile)


def roles_list(profile=None):
    """Roles list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.roles_list

    """
    return c.roles_list(__opts__, profile=profile)


def roles_get(role_name, profile=None):
    """Roles get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.roles_get <role_name>

    """
    return c.roles_get(__opts__, role_name, profile=profile)


def roles_create(role_spec, profile=None):
    """Roles create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.roles_create <role_spec>

    """
    return c.roles_create(__opts__, role_spec, profile=profile)


def roles_delete(role_name, profile=None):
    """Roles delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.roles_delete <role_name>

    """
    return c.roles_delete(__opts__, role_name, profile=profile)


def privileges_list(profile=None):
    """Privileges list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.privileges_list

    """
    return c.privileges_list(__opts__, profile=profile)


def users_list(profile=None):
    """Users list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.users_list

    """
    return c.users_list(__opts__, profile=profile)


def users_get(user_id, profile=None):
    """Users get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.users_get <user_id>

    """
    return c.users_get(__opts__, user_id, profile=profile)


def users_create(user_spec, profile=None):
    """Users create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.users_create <user_spec>

    """
    return c.users_create(__opts__, user_spec, profile=profile)


def users_update(user_id, user_spec, profile=None):
    """Users update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.users_update <user_id> <user_spec>

    """
    return c.users_update(__opts__, user_id, user_spec, profile=profile)


def users_delete(user_id, profile=None):
    """Users delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.users_delete <user_id>

    """
    return c.users_delete(__opts__, user_id, profile=profile)


def usergroups_list(profile=None):
    """Usergroups list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.usergroups_list

    """
    return c.usergroups_list(__opts__, profile=profile)


def usergroups_get(group_id, profile=None):
    """Usergroups get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.usergroups_get <group_id>

    """
    return c.usergroups_get(__opts__, group_id, profile=profile)


def usergroups_create(group_spec, profile=None):
    """Usergroups create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.usergroups_create <group_spec>

    """
    return c.usergroups_create(__opts__, group_spec, profile=profile)


def usergroups_delete(group_id, profile=None):
    """Usergroups delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_auth.usergroups_delete <group_id>

    """
    return c.usergroups_delete(__opts__, group_id, profile=profile)
