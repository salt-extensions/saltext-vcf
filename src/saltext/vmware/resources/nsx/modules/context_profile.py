"""``context_profile`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.context_profile_list"]()


def get(profile_id):
    return __resource_funcs__["nsx.context_profile_get"](profile_id)


def create(profile_id, **spec):
    return __resource_funcs__["nsx.context_profile_create"](profile_id, **spec)


def delete(profile_id):
    return __resource_funcs__["nsx.context_profile_delete"](profile_id)
