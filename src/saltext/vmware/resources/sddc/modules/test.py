"""``test`` module override for the ``sddc`` resource type."""

# pylint: disable=undefined-variable


def ping():
    return __resource_funcs__["sddc.ping"]()
