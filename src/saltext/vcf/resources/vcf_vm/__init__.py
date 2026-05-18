"""
``vcf_vm`` resource type — one virtual machine per resource ID.

Each ``vcf_vm`` resource maps to a single VM, identified by its
vCenter MOID. The VM's backing vCenter is referenced by ID so that one
minion can manage VMs across multiple vCenters without duplicating
connection credentials.

Pillar shape::

    resources:
      vcenter:
        instances:
          mgmt-vc:
            host: mgmt-vc.vcf.nimbus.internal
            username: administrator@vsphere.local
            password: VMware123!VMware123!
            verify_ssl: false
      vcf_vm:
        instances:
          web-prod-01:
            vcenter: mgmt-vc           # references resources.vcenter.instances
            moid: vm-1234              # vCenter managed object id
            labels:
              tier: production
              app: web
          web-prod-02:
            vcenter: mgmt-vc
            moid: vm-1235
            labels:
              tier: production

Once discovered, the operator can target any subset by grain::

    salt -G 'tier:production' vcf_vm.power_off
    salt -G 'app:web' vcf_vm.snapshot_create name=before-deploy

The framework injects ``__resource__["id"]`` so per-resource functions
never accept a VM identifier as an argument. ``labels`` and live vCenter
fields (name, power_state, cpu_count, memory_size_MiB) are surfaced as
grains so jq-style filtering works.

Discovery is purely pillar-driven in this resource type — auto-discovery
from vCenter is intentionally deferred to phase 10b once Salt Resources
ships discovery pagination.
"""

import logging

import requests
import urllib3

from saltext.vcf.clients import vcenter_tag
from saltext.vcf.clients import vcenter_vm
from saltext.vcf.clients import vim_vm_snapshot
from saltext.vcf.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "vcf_vm_resource"


def __virtual__():
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resource_id():
    return __resource__["id"]  # pylint: disable=undefined-variable


def _ctx():
    return __context__.get(CONTEXT_KEY, {})  # pylint: disable=undefined-variable


def _instance_cfg(resource_id):
    return _ctx().get("instances", {}).get(resource_id, {})


def _vcenter_cfg(resource_id):
    """Look up the backing vCenter connection config for the VM resource."""
    vm_cfg = _instance_cfg(resource_id)
    vcenter_id = vm_cfg.get("vcenter")
    if not vcenter_id:
        raise ValueError(f"vcf_vm resource {resource_id!r} is missing the 'vcenter' reference")
    vcenters = _ctx().get("vcenter_instances", {})
    vc_cfg = vcenters.get(vcenter_id)
    if not vc_cfg:
        raise ValueError(
            f"vcf_vm resource {resource_id!r} references unknown vcenter "
            f"{vcenter_id!r}; configured vCenters: {list(vcenters)}"
        )
    return vc_cfg


def _opts():
    """Build a clients/-compatible opts dict targeted at the current VM's vCenter."""
    return {
        "pillar": {"saltext.vcf": {"vcenter": _vcenter_cfg(_resource_id())}},
    }


def _moid():
    return _instance_cfg(_resource_id()).get("moid")


# ---------------------------------------------------------------------------
# Framework interface
# ---------------------------------------------------------------------------


def init(opts):
    """Load vcf_vm and referenced vCenter instance configs into context."""
    tree = pillar_resources_tree(opts)
    vm_instances = tree.get("vcf_vm", {}).get("instances", {})
    vcenter_instances = tree.get("vcenter", {}).get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": vm_instances,
        "vcenter_instances": vcenter_instances,
    }
    log.debug(
        "vcf_vm resource init: managing %s VMs across vCenters %s",
        len(vm_instances),
        list(vcenter_instances),
    )


def initialized():
    return _ctx().get("initialized", False)


def discover(opts):
    """Return the list of VM resource IDs declared in pillar."""
    return list(pillar_resources_tree(opts).get("vcf_vm", {}).get("instances", {}))


def grains():
    """Identity + live-from-vCenter grains for the current VM.

    Static (from pillar): ``resource_type``, ``resource_id``, ``vcenter``,
    ``moid``, plus every ``labels:`` entry promoted to a top-level grain
    so that ``salt -G 'tier:production'`` targeting works.

    Live (from vCenter): ``name``, ``power_state``, ``cpu_count``,
    ``memory_size_MiB``. Best-effort — if vCenter is unreachable we
    return only the static grains.
    """
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    g = {
        "resource_type": "vcf_vm",
        "resource_id": rid,
        "vcenter": cfg.get("vcenter", ""),
        "moid": cfg.get("moid", ""),
    }
    for key, value in (cfg.get("labels") or {}).items():
        g[str(key)] = value
    try:
        live = vcenter_vm.get(_opts(), cfg.get("moid"))
        if isinstance(live, dict):
            # /api/vcenter/vm/{id} (get-by-id) returns cpu and memory as nested
            # objects (cpu.count, memory.size_MiB), unlike the list endpoint
            # which has cpu_count/memory_size_MiB at the top level. Handle both.
            for key in ("name", "power_state"):
                if key in live:
                    g[key] = live[key]
            cpu_count = (
                (live.get("cpu") or {}).get("count")
                if isinstance(live.get("cpu"), dict)
                else live.get("cpu_count")
            )
            if cpu_count is not None:
                g["cpu_count"] = cpu_count
            memory = live.get("memory")
            mem_mib = (
                memory.get("size_MiB") if isinstance(memory, dict) else live.get("memory_size_MiB")
            )
            if mem_mib is not None:
                g["memory_size_MiB"] = mem_mib
    except (requests.RequestException, ValueError) as exc:
        log.warning("vcf_vm grains: vCenter lookup failed for %s: %s", rid, exc)
    return g


def grains_refresh():
    return grains()


def ping():
    """Probe the backing vCenter session — the VM resource is reachable iff vCenter is."""
    try:
        vc_cfg = _vcenter_cfg(_resource_id())
    except ValueError as exc:
        log.warning("vcf_vm ping: %s", exc)
        return False
    host = vc_cfg.get("host")
    verify = vc_cfg.get("verify_ssl", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.post(
            f"https://{host}/api/session",
            auth=(vc_cfg.get("username"), vc_cfg.get("password")),
            verify=verify,
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except requests.RequestException as exc:
        log.warning("vcf_vm ping failed for %s via %s: %s", _resource_id(), host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations
# ---------------------------------------------------------------------------


def info():
    """Return the full vCenter VM record."""
    return vcenter_vm.get(_opts(), _moid())


def power_state():
    """Return just the current power_state field."""
    record = vcenter_vm.get(_opts(), _moid())
    return record.get("power_state") if isinstance(record, dict) else None


def power_on():
    return vcenter_vm.power_on(_opts(), _moid())


def power_off():
    return vcenter_vm.power_off(_opts(), _moid())


def reset():
    return vcenter_vm.reset(_opts(), _moid())


def snapshot_list():
    """Return the snapshot tree (via SOAP — REST has no snapshot surface)."""
    return vim_vm_snapshot.list_(_opts(), _moid())


def snapshot_current():
    return vim_vm_snapshot.current(_opts(), _moid())


def snapshot_create(name, description="", memory=False, quiesce=False):
    return vim_vm_snapshot.create(
        _opts(),
        _moid(),
        name,
        description=description,
        memory=memory,
        quiesce=quiesce,
    )


def snapshot_revert(name, suppress_power_on=False):
    return vim_vm_snapshot.revert(_opts(), _moid(), name, suppress_power_on=suppress_power_on)


def snapshot_remove(name, remove_children=False):
    return vim_vm_snapshot.remove(_opts(), _moid(), name, remove_children=remove_children)


def snapshot_remove_all():
    return vim_vm_snapshot.remove_all(_opts(), _moid())


def tag_assign(tag_id):
    """Assign vCenter tag *tag_id* to this VM."""
    return vcenter_tag.assign(_opts(), tag_id, "VirtualMachine", _moid())


def tag_list_assigned():
    return vcenter_tag.list_assigned(_opts(), "VirtualMachine", _moid())
