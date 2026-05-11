"""``tag`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcenter.tag_list"]()


def create(name, category_id, description=""):
    return __resource_funcs__["vcenter.tag_create"](name, category_id, description=description)


def delete(tag):
    return __resource_funcs__["vcenter.tag_delete"](tag)


def assign(tag, object_type, object_id):
    return __resource_funcs__["vcenter.tag_assign"](tag, object_type, object_id)


def list_assigned(object_type, object_id):
    return __resource_funcs__["vcenter.tag_list_assigned"](object_type, object_id)
