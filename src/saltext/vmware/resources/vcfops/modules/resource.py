"""``resource`` module for the ``vcf_ops`` resource type."""

# pylint: disable=undefined-variable


def list_(page=0, page_size=1000, **filters):
    return __resource_funcs__["vcf_ops.resource_list"](page=page, page_size=page_size, **filters)


def get(resource_id):
    return __resource_funcs__["vcf_ops.resource_get"](resource_id)


def relationships(resource_id, **filters):
    return __resource_funcs__["vcf_ops.resource_relationships"](resource_id, **filters)


def stats(resource_id, **filters):
    return __resource_funcs__["vcf_ops.resource_stats"](resource_id, **filters)
