"""``cluster`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def status():
    return __resource_funcs__["nsx.cluster_status"]()
