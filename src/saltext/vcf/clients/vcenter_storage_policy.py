"""Client for vCenter Storage Policy-Based Management.

Note: the vSphere REST SPBM API (``/api/vcenter/storage/policies``) is
read-only and has no per-policy GET path. Policies are a synthesized view of
profiles from multiple underlying sources (built-in VMC profiles, vSAN,
vVol, user-authored) and are exposed only as an enumerable, filterable list.
:func:`get` is implemented in terms of the filter query parameter
(``?policies=<id>``) which returns a single-element list when the id
matches.

Authoring (create/update/delete) a tag/capability-based policy has never
been exposed over REST — that's only reachable through the PBM SOAP service
(:mod:`saltext.vcf.utils.pbm`), the same one PowerCLI's
``New-/Set-/Remove-SpbmStoragePolicy`` wrap.
"""

import requests
from pyVmomi import pbm

from saltext.vcf.utils import pbm as pbm_utils
from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/storage/policies"

# Namespace/id PBM uses to represent tag-based constraints (vs. capability
# constraints, which use their own vendor namespace per capability).
_TAGS_ID = "com.vmware.storage.tag"
_TAGS_NS = "https://www.vmware.com/storage/tag"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, policy, profile=None):
    """Return the single policy with id *policy*.

    Implemented via the filter query parameter since the SPBM REST API has
    no per-id GET path. Raises :class:`requests.HTTPError` 404 when the
    policy is unknown.
    """
    result = vcenter.api_get(opts, PATH, params={"policies": policy}, profile=profile)
    if isinstance(result, list) and result:
        return result[0]
    resp = requests.Response()
    resp.status_code = 404
    raise requests.HTTPError("storage policy not found", response=resp)


def get_or_none(opts, policy, profile=None):
    try:
        return get(opts, policy, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_by_name(opts, name, profile=None):
    """Return ``{"id", "name", "description", "constraints"}`` for the
    user-authored policy *name*, via PBM (so constraints are readable), or
    ``None`` if it doesn't exist.
    """
    pm = pbm_utils.profile_manager(opts, profile=profile)
    p = _find_profile(pm, name)
    if p is None:
        return None
    return {
        "id": p.profileId.uniqueId,
        "name": p.name,
        "description": p.description,
        "constraints": _from_subprofiles(p),
    }


def create(opts, name, constraints, description=None, profile=None):
    """Create a tag/capability-based storage policy and return its id.

    *constraints* is a list of rulesets, each an optional
    ``{"capabilities": {...}, "tags": {...}}`` dict. Rulesets are OR-ed by
    the server when evaluating the policy; capabilities/tags within one
    ruleset are AND-ed. See :func:`_to_subprofiles`.
    """
    pm = pbm_utils.profile_manager(opts, profile=profile)
    resource_type = pbm.profile.ResourceTypeEnum.STORAGE  # pylint: disable=no-member
    spec = pbm.profile.CapabilityBasedProfileCreateSpec(
        name=name,
        description=description,
        resourceType=pbm.profile.ResourceType(resourceType=resource_type),
        constraints=pbm.profile.SubProfileCapabilityConstraints(
            subProfiles=_to_subprofiles(constraints)
        ),
    )
    new_id = pm.PbmCreate(createSpec=spec)
    return new_id.uniqueId


def update(opts, name, constraints=None, description=None, profile=None):
    """Update an existing policy's *description* and/or *constraints*.

    Fields left as ``None`` are unchanged.
    """
    pm = pbm_utils.profile_manager(opts, profile=profile)
    p = _find_profile(pm, name)
    if p is None:
        raise LookupError(f"storage policy {name!r} not found")
    spec = pbm.profile.CapabilityBasedProfileUpdateSpec(
        description=description if description is not None else p.description,
        constraints=(
            pbm.profile.SubProfileCapabilityConstraints(subProfiles=_to_subprofiles(constraints))
            if constraints is not None
            else p.constraints
        ),
    )
    pm.PbmUpdate(profileId=p.profileId, updateSpec=spec)


def delete(opts, name, profile=None):
    """Delete the user-authored policy *name*."""
    pm = pbm_utils.profile_manager(opts, profile=profile)
    p = _find_profile(pm, name)
    if p is None:
        raise LookupError(f"storage policy {name!r} not found")
    pm.PbmDelete(profileId=[p.profileId])


def default_policy_get(opts, datastore, profile=None):
    """Return the uniqueId of the default storage policy assigned to
    *datastore* (by name), via PBM ``PbmQueryDefaultRequirementProfile``.
    """
    pm = pbm_utils.profile_manager(opts, profile=profile)
    hub = pbm.placement.PlacementHub(
        hubType="Datastore", hubId=_find_datastore_id(opts, datastore, profile=profile)
    )
    spec = pm.PbmQueryDefaultRequirementProfile(hub=hub)
    return spec.uniqueId if spec else None


def default_policy_set(opts, datastore, policy_name, profile=None):
    """Assign the existing named policy *policy_name* as the default storage
    policy for *datastore* (PBM ``PbmAssignDefaultRequirementProfile``).
    """
    pm = pbm_utils.profile_manager(opts, profile=profile)
    p = _find_profile(pm, policy_name)
    if p is None:
        raise LookupError(f"storage policy {policy_name!r} not found")
    hub = pbm.placement.PlacementHub(
        hubType="Datastore", hubId=_find_datastore_id(opts, datastore, profile=profile)
    )
    pm.PbmAssignDefaultRequirementProfile(profile=p.profileId, datastores=[hub])


def _find_datastore_id(opts, name, profile=None):
    """Resolve a datastore name to its vAPI/moId string via the REST list.

    PBM's ``PlacementHub.hubId`` expects the same MoRef-shaped id the vAPI
    datastore list already returns (e.g. ``datastore-12``) — no separate
    SOAP lookup needed.
    """
    for d in vcenter.api_get(opts, "/api/vcenter/datastore", profile=profile):
        if d.get("name") == name:
            return d["datastore"]
    raise LookupError(f"datastore {name!r} not found")


def _find_profile(pm, name):
    resource_type = pbm.profile.ResourceTypeEnum.STORAGE  # pylint: disable=no-member
    ids = pm.PbmQueryProfile(
        resourceType=pbm.profile.ResourceType(resourceType=resource_type),
        profileCategory=pbm.profile.CapabilityBasedProfile.ProfileCategoryEnum.REQUIREMENT,
    )
    if not ids:
        return None
    for p in pm.PbmRetrieveContent(profileIds=ids):
        if p.name == name:
            return p
    return None


def _to_subprofiles(rulesets):
    """Turn the user-friendly ``constraints`` shape into PBM subprofiles."""
    res = []
    for ruleset in rulesets or []:
        capability_spec = ruleset.get("capabilities")
        tag_spec = ruleset.get("tags")
        rules = []

        if capability_spec:
            for capability, value in capability_spec.items():
                namespace, _, cap_name = capability.partition(".")
                rules.append(
                    pbm.capability.CapabilityInstance(
                        id=pbm.capability.CapabilityMetadata.UniqueId(
                            namespace=namespace, id=cap_name
                        ),
                        constraint=[
                            pbm.capability.ConstraintInstance(
                                propertyInstance=[
                                    pbm.capability.PropertyInstance(id=cap_name, value=value)
                                ]
                            )
                        ],
                    )
                )

        if tag_spec:
            for category, tags in tag_spec.items():
                operator = None
                if category.startswith("!"):
                    category = category[1:]
                    operator = pbm.capability.Operator.NOT  # pylint: disable=no-member
                rules.append(
                    pbm.capability.CapabilityInstance(
                        id=pbm.capability.CapabilityMetadata.UniqueId(
                            namespace=_TAGS_NS, id=category
                        ),
                        constraint=[
                            pbm.capability.ConstraintInstance(
                                propertyInstance=[
                                    pbm.capability.PropertyInstance(
                                        id=f"{_TAGS_ID}.{category}.property",
                                        operator=operator,
                                        value=pbm.capability.types.DiscreteSet(values=list(tags)),
                                    )
                                ]
                            )
                        ],
                    )
                )

        if rules:
            res.append(pbm.profile.SubProfileCapabilityConstraints.SubProfile(capability=rules))
    return res


def _from_subprofiles(p):
    """Inverse of :func:`_to_subprofiles`, for reading back a policy's constraints."""
    if not isinstance(p.constraints, pbm.profile.SubProfileCapabilityConstraints):
        return None
    res = []
    for sub in p.constraints.subProfiles:
        capabilities = {}
        tags = {}
        for capability in sub.capability:
            namespace = capability.id.namespace
            cap_name = capability.id.id
            constraint = capability.constraint[0].propertyInstance[0]
            if namespace == _TAGS_NS:
                name = cap_name
                if constraint.operator == pbm.capability.Operator.NOT:  # pylint: disable=no-member
                    name = "!" + name
                tags[name] = sorted(constraint.value.values)
            else:
                capabilities[f"{namespace}.{cap_name}"] = constraint.value
        ruleset = {}
        if capabilities:
            ruleset["capabilities"] = capabilities
        if tags:
            ruleset["tags"] = tags
        res.append(ruleset)
    return res
