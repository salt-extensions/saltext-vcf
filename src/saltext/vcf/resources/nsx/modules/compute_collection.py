"""``compute_collection`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.compute_collection_list"]()


def get(collection_id):
    return __resource_funcs__["nsx.compute_collection_get"](collection_id)
