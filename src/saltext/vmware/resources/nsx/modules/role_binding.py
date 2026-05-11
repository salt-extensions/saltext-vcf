"""``role_binding`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.role_binding_list"]()


def get(binding_id):
    return __resource_funcs__["nsx.role_binding_get"](binding_id)


def create(name, type_, roles, **spec):
    return __resource_funcs__["nsx.role_binding_create"](name, type_, roles, **spec)


def update(binding_id, body):
    return __resource_funcs__["nsx.role_binding_update"](binding_id, body)


def delete(binding_id):
    return __resource_funcs__["nsx.role_binding_delete"](binding_id)
