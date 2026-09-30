"""State module for vCenter tag categories (``vmware_tag.present_category`` parity)."""

from saltext.vcf.clients import vcenter_tag_category as c

__virtualname__ = "vcf_vcenter_tag_category"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(
    name,
    cardinality="SINGLE",
    associable_types=None,
    description="",
    profile=None,
):
    """Ensure tag category *name* exists with the given constraints.

    .. code-block:: yaml

        Tag category present:
          vcf_vcenter_tag_category.present:
            - name: environment
            - cardinality: SINGLE
            - associable_types:
                - VirtualMachine
                - ClusterComputeResource
    """
    ret = _ret(name)
    existing = c.by_name(__opts__, name, profile=profile)
    if existing is not None:
        drift = {}
        if existing.get("cardinality") != cardinality:
            drift["cardinality"] = (existing.get("cardinality"), cardinality)
        if description is not None and existing.get("description") != description:
            drift["description"] = (existing.get("description"), description)
        if associable_types is not None and sorted(existing.get("associable_types") or []) != sorted(
            associable_types
        ):
            drift["associable_types"] = (
                existing.get("associable_types"),
                list(associable_types),
            )
        if not drift:
            ret["comment"] = f"tag category {name!r} already matches."
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"tag category {name!r} would be updated: {sorted(drift)}."
            ret["changes"] = drift
            return ret
        spec = {}
        if "description" in drift:
            spec["description"] = description
        if "associable_types" in drift:
            spec["associable_types"] = list(associable_types)
        if spec:
            c.update(__opts__, existing["id"], spec, profile=profile)
        ret["changes"] = drift
        ret["comment"] = f"tag category {name!r} updated."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"tag category {name!r} would be created."
        ret["changes"] = {"new": name}
        return ret
    c.create(
        __opts__,
        name,
        cardinality=cardinality,
        description=description or "",
        associable_types=associable_types,
        profile=profile,
    )
    ret["changes"] = {"new": name}
    ret["comment"] = f"tag category {name!r} created."
    return ret


def absent(name, profile=None):
    """Ensure tag category *name* does not exist.

    .. code-block:: yaml

        Tag category absent:
          vcf_vcenter_tag_category.absent:
            - name: environment
    """
    ret = _ret(name)
    existing = c.by_name(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"tag category {name!r} already absent."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"tag category {name!r} would be removed."
        ret["changes"] = {"old": name}
        return ret
    c.delete(__opts__, existing["id"], profile=profile)
    ret["changes"] = {"old": name}
    ret["comment"] = f"tag category {name!r} removed."
    return ret
