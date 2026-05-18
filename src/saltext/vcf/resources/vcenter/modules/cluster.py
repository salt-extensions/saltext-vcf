"""``cluster`` module for the ``vcenter`` resource type.

Loaded only for jobs dispatched to vCenter resources. Delegates to
:mod:`saltext.vcf.resources.vcenter` via ``__resource_funcs__``.
"""

# pylint: disable=undefined-variable


def list_():
    """List clusters on the targeted vCenter."""
    return __resource_funcs__["vcenter.cluster_list"]()


def get(cluster):
    """Return one cluster by id on the targeted vCenter."""
    return __resource_funcs__["vcenter.cluster_get"](cluster)


def create(name, datacenter=None, **spec):
    """Create a cluster on the targeted vCenter."""
    return __resource_funcs__["vcenter.cluster_create"](name, datacenter=datacenter, **spec)


def delete(cluster):
    """Delete a cluster on the targeted vCenter."""
    return __resource_funcs__["vcenter.cluster_delete"](cluster)
