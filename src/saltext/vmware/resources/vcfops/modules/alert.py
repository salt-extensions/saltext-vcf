"""``alert`` module for the ``vcf_ops`` resource type."""

# pylint: disable=undefined-variable


def definitions_list(page=0, page_size=1000):
    return __resource_funcs__["vcf_ops.alert_definitions_list"](page=page, page_size=page_size)


def definition_get(alert_id):
    return __resource_funcs__["vcf_ops.alert_definition_get"](alert_id)


def symptoms_list(page=0, page_size=1000):
    return __resource_funcs__["vcf_ops.symptom_definitions_list"](page=page, page_size=page_size)
