"""Client for vCenter SSO identity APIs under ``/api/vcenter/identity``.

Covers the vSphere 9 SSO identity surface used for platform authentication:
external identity providers (Active Directory / LDAP / OIDC federation), and
the local ``vsphere.local`` group and user CRUD endpoints.

Auth is delegated to :mod:`saltext.vcf.utils.vcenter` which manages the
``/api/session`` token session.
"""

import requests

from saltext.vcf.utils import vcenter

# ---------------------------------------------------------------------------
# Identity providers
# ---------------------------------------------------------------------------

_PROVIDERS = "/api/vcenter/identity/providers"


def providers_list(opts, profile=None):
    """Return the list of registered identity providers."""
    return vcenter.api_get(opts, _PROVIDERS, profile=profile)


def providers_get(opts, provider_id, profile=None):
    """Return a single identity provider by id."""
    return vcenter.api_get(opts, f"{_PROVIDERS}/{provider_id}", profile=profile)


def providers_get_or_none(opts, provider_id, profile=None):
    """Return the provider or ``None`` if it does not exist."""
    try:
        return providers_get(opts, provider_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def providers_create(opts, spec, profile=None):
    """Create a new identity provider.

    *spec* is passed through as the POST body; typical keys include
    ``config_tag`` (``ActiveDirectory``, ``LDAP``, ``Oauth2``, ``Oidc``),
    ``domain_name``, ``auth_type``, ``username``, ``password``, and any
    provider-specific ``*_configuration`` block.
    """
    return vcenter.api_post(opts, _PROVIDERS, body=dict(spec), profile=profile)


def providers_update(opts, provider_id, spec, profile=None):
    """PATCH an existing identity provider."""
    return vcenter.api_patch(opts, f"{_PROVIDERS}/{provider_id}", body=dict(spec), profile=profile)


def providers_delete(opts, provider_id, profile=None):
    """Delete an identity provider by id."""
    return vcenter.api_delete(opts, f"{_PROVIDERS}/{provider_id}", profile=profile)


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

_GROUPS = "/api/vcenter/identity/groups"


def groups_list(opts, domain=None, profile=None):
    """List groups, optionally filtered to a specific ``domain``."""
    params = {"domain": domain} if domain else None
    return vcenter.api_get(opts, _GROUPS, params=params, profile=profile)


def groups_get(opts, group, profile=None):
    """Return a single group by id."""
    return vcenter.api_get(opts, f"{_GROUPS}/{group}", profile=profile)


def groups_get_or_none(opts, group, profile=None):
    """Return the group or ``None`` if it does not exist."""
    try:
        return groups_get(opts, group, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def groups_create(opts, name, domain, description="", profile=None):
    """Create a group in *domain*.

    Extra fields (e.g. initial members) may be provided by the caller wrapping
    them via ``spec``; this helper covers the common ``name`` / ``domain`` /
    ``description`` shape used against ``vsphere.local``.
    """
    body = {"name": name, "domain": domain, "description": description}
    return vcenter.api_post(opts, _GROUPS, body=body, profile=profile)


def groups_update(opts, group, spec, profile=None):
    """PATCH a group. *spec* accepts ``description`` and other mutable fields."""
    return vcenter.api_patch(opts, f"{_GROUPS}/{group}", body=dict(spec), profile=profile)


def groups_delete(opts, group, profile=None):
    """Delete a group by id."""
    return vcenter.api_delete(opts, f"{_GROUPS}/{group}", profile=profile)


def group_add_member(opts, group, member, profile=None):
    """Add a user or nested group to *group*.

    *member* is the fully-qualified principal (``user@domain`` or the SSO
    group id); vSphere accepts either a user or a group here.
    """
    body = {"members_to_add": [member]}
    return vcenter.api_patch(opts, f"{_GROUPS}/{group}/members", body=body, profile=profile)


def group_remove_member(opts, group, member, profile=None):
    """Remove a member from *group*."""
    body = {"members_to_remove": [member]}
    return vcenter.api_patch(opts, f"{_GROUPS}/{group}/members", body=body, profile=profile)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

_USERS = "/api/vcenter/identity/users"


def users_list(opts, domain=None, profile=None):
    """List users, optionally filtered to a specific ``domain``."""
    params = {"domain": domain} if domain else None
    return vcenter.api_get(opts, _USERS, params=params, profile=profile)


def users_get(opts, user, profile=None):
    """Return a single user by id."""
    return vcenter.api_get(opts, f"{_USERS}/{user}", profile=profile)


def users_get_or_none(opts, user, profile=None):
    """Return the user or ``None`` if it does not exist."""
    try:
        return users_get(opts, user, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def users_create(opts, username, domain, password, description="", email=None, profile=None):
    """Create a local SSO user.

    Only supported against the local (``vsphere.local``) domain; external
    identity providers manage their own users.
    """
    body = {
        "username": username,
        "domain": domain,
        "password": password,
        "description": description,
    }
    if email is not None:
        body["email"] = email
    return vcenter.api_post(opts, _USERS, body=body, profile=profile)


def users_update(opts, user, spec, profile=None):
    """PATCH a user. *spec* accepts ``password``, ``description``, ``email`` etc."""
    return vcenter.api_patch(opts, f"{_USERS}/{user}", body=dict(spec), profile=profile)


def users_delete(opts, user, profile=None):
    """Delete a user by id."""
    return vcenter.api_delete(opts, f"{_USERS}/{user}", profile=profile)
