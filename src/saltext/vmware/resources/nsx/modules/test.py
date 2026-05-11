"""``test`` module override for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def ping():
    return __resource_funcs__["nsx.ping"]()
