"""State module for vCenter tags (``vmware_tag`` parity)."""

from saltext.vcf.clients import vcenter_tag as c
from saltext.vcf.clients import vcenter_tag_category as cat_c

__virtualname__ = "vcf_vcenter_tag"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(
    name,
    category,
    description="",
    profile=None,
):
    """Ensure tag *name* exists in *category* (category name or id).

    .. code-block:: yaml

        Tag present:
          vcf_vcenter_tag.present:
            - name: env-prod
            - category: environment
            - description: production
    """
    ret = _ret(name)
    category_id = _resolve_category(category, profile=profile)
    if category_id is None:
        ret["result"] = False
        ret["comment"] = f"tag category {category!r} not found"
        return ret
    existing = _find_in_category(name, category_id, profile=profile)
    if existing is not None:
        drift = {}
        if description is not None and existing.get("description") != description:
            drift["description"] = (existing.get("description"), description)
        if not drift:
            ret["comment"] = f"tag {name!r} already present in category {category!r}."
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"tag {name!r} would be updated: {sorted(drift)}."
            ret["changes"] = drift
            return ret
        c.update(__opts__, existing["id"], {"description": description}, profile=profile)
        ret["changes"] = drift
        ret["comment"] = f"tag {name!r} updated."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"tag {name!r} would be created in category {category!r}."
        ret["changes"] = {"new": name}
        return ret
    c.create(__opts__, name, category_id, description=description or "", profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"tag {name!r} created in category {category!r}."
    return ret


def absent(name, profile=None):
    """Ensure tag *name* does not exist.

    .. code-block:: yaml

        Tag absent:
          vcf_vcenter_tag.absent:
            - name: env-prod
    """
    ret = _ret(name)
    found = None
    for tag in c.list_(__opts__, profile=profile) or []:
        if tag.get("name") == name:
            found = tag
            break
    if found is None:
        ret["comment"] = f"tag {name!r} already absent."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"tag {name!r} would be removed."
        ret["changes"] = {"old": name}
        return ret
    c.delete(__opts__, found["id"], profile=profile)
    ret["changes"] = {"old": name}
    ret["comment"] = f"tag {name!r} removed."
    return ret


def _resolve_category(category, profile=None):
    """Accept either a category *name* or a category id; return the id.

    Unresolvable values (neither a known name nor an existing id) return
    ``None`` so the state can fail cleanly instead of creating a tag
    under a bogus category.
    """
    if category is None:
        return None
    cat = cat_c.by_name(__opts__, category, profile=profile)
    if cat is not None:
        return cat["id"]
    if cat_c.get_or_none(__opts__, category, profile=profile) is not None:
        return category
    return None


def _find_in_category(name, category_id, profile=None):
    for tag in c.list_(__opts__, profile=profile) or []:
        if tag.get("name") != name:
            continue
        info = c.get(__opts__, tag["id"], profile=profile)
        if info.get("category_id") == category_id:
            return info
    return None
