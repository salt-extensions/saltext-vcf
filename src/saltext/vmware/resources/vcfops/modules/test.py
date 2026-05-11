"""``test`` module override for the ``vcf_ops`` resource type."""

# pylint: disable=undefined-variable


def ping():
    return __resource_funcs__["vcf_ops.ping"]()
