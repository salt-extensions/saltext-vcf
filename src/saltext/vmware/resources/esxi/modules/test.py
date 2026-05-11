"""``test`` module override for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def ping():
    return __resource_funcs__["esxi.ping"]()
