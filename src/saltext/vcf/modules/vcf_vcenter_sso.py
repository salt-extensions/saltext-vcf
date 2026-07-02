"""Execution module for vCenter SSO identity management.

Wraps :mod:`saltext.vcf.clients.vcenter_sso` for identity provider, group,
and user administration on vSphere 9 vCenter.
"""

from saltext.vcf.clients import vcenter_sso as r

__virtualname__ = "vcf_vcenter_sso"


def __virtual__():
    return __virtualname__


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


def providers_list(profile=None):
    """List identity providers.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.providers_list

    """
    return r.providers_list(__opts__, profile=profile)


def providers_get(provider_id, profile=None):
    """Return a single identity provider by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.providers_get <provider_id>

    """
    return r.providers_get(__opts__, provider_id, profile=profile)


def providers_get_or_none(provider_id, profile=None):
    """Return the provider or ``None`` if missing.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.providers_get_or_none <provider_id>

    """
    return r.providers_get_or_none(__opts__, provider_id, profile=profile)


def providers_create(spec, profile=None):
    """Create an identity provider from *spec*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.providers_create spec='{"config_tag": "ActiveDirectory", "domain_name": "corp.example"}'

    """
    return r.providers_create(__opts__, spec, profile=profile)


def providers_update(provider_id, spec, profile=None):
    """PATCH an identity provider.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.providers_update <provider_id> spec='{"username": "svc"}'

    """
    return r.providers_update(__opts__, provider_id, spec, profile=profile)


def providers_delete(provider_id, profile=None):
    """Delete an identity provider.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.providers_delete <provider_id>

    """
    return r.providers_delete(__opts__, provider_id, profile=profile)


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


def groups_list(domain=None, profile=None):
    """List groups, optionally filtered by *domain*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.groups_list domain=vsphere.local

    """
    return r.groups_list(__opts__, domain=domain, profile=profile)


def groups_get(group, profile=None):
    """Return a group by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.groups_get <group>

    """
    return r.groups_get(__opts__, group, profile=profile)


def groups_get_or_none(group, profile=None):
    """Return the group or ``None`` if missing.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.groups_get_or_none <group>

    """
    return r.groups_get_or_none(__opts__, group, profile=profile)


def groups_create(name, domain, description="", profile=None):
    """Create a group.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.groups_create <name> <domain> <description>

    """
    return r.groups_create(__opts__, name, domain, description=description, profile=profile)


def groups_update(group, spec, profile=None):
    """PATCH a group.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.groups_update <group> spec='{"description": "new"}'

    """
    return r.groups_update(__opts__, group, spec, profile=profile)


def groups_delete(group, profile=None):
    """Delete a group by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.groups_delete <group>

    """
    return r.groups_delete(__opts__, group, profile=profile)


def group_add_member(group, member, profile=None):
    """Add a member to a group.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.group_add_member <group> <member>

    """
    return r.group_add_member(__opts__, group, member, profile=profile)


def group_remove_member(group, member, profile=None):
    """Remove a member from a group.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.group_remove_member <group> <member>

    """
    return r.group_remove_member(__opts__, group, member, profile=profile)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def users_list(domain=None, profile=None):
    """List users, optionally filtered by *domain*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.users_list domain=vsphere.local

    """
    return r.users_list(__opts__, domain=domain, profile=profile)


def users_get(user, profile=None):
    """Return a user by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.users_get <user>

    """
    return r.users_get(__opts__, user, profile=profile)


def users_get_or_none(user, profile=None):
    """Return the user or ``None`` if missing.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.users_get_or_none <user>

    """
    return r.users_get_or_none(__opts__, user, profile=profile)


def users_create(username, domain, password, description="", email=None, profile=None):
    """Create a local SSO user.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.users_create alice vsphere.local <password>

    """
    return r.users_create(
        __opts__,
        username,
        domain,
        password,
        description=description,
        email=email,
        profile=profile,
    )


def users_update(user, spec, profile=None):
    """PATCH a user.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.users_update <user> spec='{"description": "new"}'

    """
    return r.users_update(__opts__, user, spec, profile=profile)


def users_delete(user, profile=None):
    """Delete a user by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_sso.users_delete <user>

    """
    return r.users_delete(__opts__, user, profile=profile)
