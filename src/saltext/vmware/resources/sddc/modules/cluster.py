"""``cluster`` module for the ``sddc`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["sddc.cluster_list"]()


def get(cluster):
    return __resource_funcs__["sddc.cluster_get"](cluster)


def create(cluster_spec):
    return __resource_funcs__["sddc.cluster_create"](cluster_spec)


def delete(cluster):
    return __resource_funcs__["sddc.cluster_delete"](cluster)
