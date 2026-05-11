"""SDDC Manager local users + roles (/v1/users, /v1/roles)."""

import requests

from saltext.vmware.utils import sddc

USERS = "/v1/users"
ROLES = "/v1/roles"


def list_users(opts, profile=None):
    return sddc.api_get(opts, USERS, profile=profile)


def list_roles(opts, profile=None):
    return sddc.api_get(opts, ROLES, profile=profile)


def get_user(opts, user_id, profile=None):
    return sddc.api_get(opts, f"{USERS}/{user_id}", profile=profile)


def get_user_or_none(opts, user_id, profile=None):
    try:
        return get_user(opts, user_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def add_users(opts, users, profile=None):
    """Bulk-add users. *users* is a list of ``UserCreationSpec`` dicts."""
    return sddc.api_post(opts, USERS, body=list(users), profile=profile)


def delete_user(opts, user_id, profile=None):
    return sddc.api_delete(opts, f"{USERS}/{user_id}", profile=profile)
