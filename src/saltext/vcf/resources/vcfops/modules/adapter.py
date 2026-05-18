"""``adapter`` module for the ``vcf_ops`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcf_ops.adapter_list"]()


def get(kind_key):
    return __resource_funcs__["vcf_ops.adapter_get"](kind_key)
