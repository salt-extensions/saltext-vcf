"""VCF Operations — identity (auth sources, roles, users, groups, privileges).

These endpoints cover the Suite-API ``/suite-api/api/auth/*`` surface:

- ``/auth/sources`` — identity sources (LOCAL, AD/LDAP, OIDC, ...)
- ``/auth/roles`` — RBAC roles (10 system roles in the lab)
- ``/auth/privileges`` — the catalog of privileges roles map onto
- ``/auth/users`` — local + imported users
- ``/auth/usergroups`` — user groups

Note: ``/auth/permissions`` is intentionally absent — the lab build
returns 404 for that path.
"""

import requests

from saltext.vmware.utils import vcfops

_SOURCES = "/suite-api/api/auth/sources"
_ROLES = "/suite-api/api/auth/roles"
_PRIVILEGES = "/suite-api/api/auth/privileges"
_USERS = "/suite-api/api/auth/users"
_USERGROUPS = "/suite-api/api/auth/usergroups"


def sources_list(opts, profile=None):
    return vcfops.api_get(opts, _SOURCES, profile=profile)


def sources_get(opts, source_id, profile=None):
    return vcfops.api_get(opts, f"{_SOURCES}/{source_id}", profile=profile)


def sources_get_or_none(opts, source_id, profile=None):
    try:
        return sources_get(opts, source_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def roles_list(opts, profile=None):
    return vcfops.api_get(opts, _ROLES, profile=profile)


def roles_get(opts, role_name, profile=None):
    return vcfops.api_get(opts, f"{_ROLES}/{role_name}", profile=profile)


def roles_get_or_none(opts, role_name, profile=None):
    try:
        return roles_get(opts, role_name, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def roles_create(opts, role_spec, profile=None):
    """Create a custom role. *role_spec* per the Suite-API.

    Required fields: ``name``, ``displayName``, ``description``,
    ``privilege-keys`` (list of privilege identifiers).
    """
    return vcfops.api_post(opts, _ROLES, body=role_spec, profile=profile)


def roles_delete(opts, role_name, profile=None):
    return vcfops.api_delete(opts, f"{_ROLES}/{role_name}", profile=profile)


def privileges_list(opts, profile=None):
    return vcfops.api_get(opts, _PRIVILEGES, profile=profile)


def users_list(opts, profile=None):
    return vcfops.api_get(opts, _USERS, profile=profile)


def users_get(opts, user_id, profile=None):
    return vcfops.api_get(opts, f"{_USERS}/{user_id}", profile=profile)


def users_get_or_none(opts, user_id, profile=None):
    try:
        return users_get(opts, user_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def users_create(opts, user_spec, profile=None):
    """Create a local user.

    *user_spec* example::

        {"username": "alice", "firstName": "...", "lastName": "...",
         "password": "...", "emailAddress": "...", "roleNames": ["Admin"]}
    """
    return vcfops.api_post(opts, _USERS, body=user_spec, profile=profile)


def users_update(opts, user_id, user_spec, profile=None):
    return vcfops.api_put(opts, f"{_USERS}/{user_id}", body=user_spec, profile=profile)


def users_delete(opts, user_id, profile=None):
    return vcfops.api_delete(opts, f"{_USERS}/{user_id}", profile=profile)


def usergroups_list(opts, profile=None):
    return vcfops.api_get(opts, _USERGROUPS, profile=profile)


def usergroups_get(opts, group_id, profile=None):
    return vcfops.api_get(opts, f"{_USERGROUPS}/{group_id}", profile=profile)


def usergroups_get_or_none(opts, group_id, profile=None):
    try:
        return usergroups_get(opts, group_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def usergroups_create(opts, group_spec, profile=None):
    return vcfops.api_post(opts, _USERGROUPS, body=group_spec, profile=profile)


def usergroups_delete(opts, group_id, profile=None):
    return vcfops.api_delete(opts, f"{_USERGROUPS}/{group_id}", profile=profile)
