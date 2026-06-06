"""Resource layer for vCenter VMs (/api/vcenter/vm)."""

import socket
import time

import requests

from saltext.vcf.clients import vcenter_cluster
from saltext.vcf.clients import vcenter_datacenter
from saltext.vcf.clients import vcenter_host
from saltext.vcf.clients import vim_vm
from saltext.vcf.clients import vim_vm_customization
from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/vm"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, vm, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{vm}", profile=profile)


def get_or_none(opts, vm, profile=None):
    try:
        return get(opts, vm, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_by_name(opts, name, profile=None):
    matches = search(opts, names=[name], profile=profile)
    for vm in matches:
        if vm.get("name") == name:
            return vm
    return None


def _power(opts, vm, action, profile=None):
    return vcenter.api_post(opts, f"{PATH}/{vm}/power", params={"action": action}, profile=profile)


def power_on(opts, vm, profile=None):
    return _power(opts, vm, "start", profile=profile)


def power_off(opts, vm, profile=None):
    return _power(opts, vm, "stop", profile=profile)


def reset(opts, vm, profile=None):
    return _power(opts, vm, "reset", profile=profile)


def deploy(opts, name, spec, profile=None):
    """Deploy a VM for PoC validation.

    Supports cloning from an existing template/source VM when ``template`` or
    ``source`` is provided. Without a source, creates a bare VM.
    """
    source = spec.get("source") or spec.get("template")
    if source:
        customization = _customization_spec(spec)
        return {
            "task": vim_vm.clone(
                opts,
                source,
                name,
                folder=spec.get("folder"),
                datastore=spec.get("datastore"),
                host=spec.get("host"),
                resource_pool=spec.get("resource_pool"),
                cluster=spec.get("cluster"),
                power_on=spec.get("power_on", True),
                cpu_count=spec.get("cpu_count"),
                memory_mb=spec.get("memory_mb"),
                annotation=spec.get("annotation"),
                customization=customization,
                profile=profile,
            )
        }
    return {
        "task": vim_vm.create(
            opts,
            name,
            spec["folder"],
            spec["datastore"],
            cpu_count=spec.get("cpu_count", 1),
            memory_mb=spec.get("memory_mb", 1024),
            guest_id=spec.get("guest_id", "otherGuest64"),
            cluster=spec.get("cluster"),
            host=spec.get("host"),
            resource_pool=spec.get("resource_pool"),
            annotation=spec.get("annotation", ""),
            profile=profile,
        )
    }


def wait_reachable(target_ip, port=22, timeout=120, interval=10):
    deadline = time.monotonic() + float(timeout)
    while True:
        try:
            with socket.create_connection((target_ip, int(port)), timeout=min(float(interval), 10)):
                return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(float(interval))


def _customization_spec(spec):
    customization = spec.get("customization")
    if not customization:
        return None
    ctype = customization.get("type", "linux")
    if ctype != "linux":
        raise ValueError(f"unsupported VM customization type {ctype!r}")
    return vim_vm_customization.linux_spec(
        customization.get("hostname") or spec.get("vm_name") or spec.get("name"),
        customization["domain"],
        time_zone=customization.get("time_zone", "UTC"),
        nics=customization.get("nics"),
        dns_servers=customization.get("dns_servers"),
        dns_search_path=customization.get("dns_search_path"),
    )


_FILTER_KEYS = (
    ("power_states", "power_states"),
    ("names", "names"),
    ("hosts", "hosts"),
    ("clusters", "clusters"),
    ("folders", "folders"),
    ("datacenters", "datacenters"),
    ("resource_pools", "resource_pools"),
    ("vms", "vms"),
)


def search(
    opts,
    *,
    power_states=None,
    names=None,
    hosts=None,
    clusters=None,
    folders=None,
    datacenters=None,
    resource_pools=None,
    vms=None,
    profile=None,
):
    """Server-side VM filtering via ``/api/vcenter/vm?<filter>=...``.

    Each filter accepts a list (sent as repeated query keys). All filters are
    AND-combined by the server. ``power_states`` values: ``POWERED_ON``,
    ``POWERED_OFF``, ``SUSPENDED``.

    vCenter 9 uses flat parameter names (e.g. ``power_states=POWERED_ON``);
    earlier versions used ``filter.power_states=...``.
    """
    locals_ = locals()
    params = {}
    for key, query_name in _FILTER_KEYS:
        val = locals_.get(key)
        if val:
            params[query_name] = list(val)
    return vcenter.api_get(opts, PATH, params=params or None, profile=profile)


def tree(opts, profile=None):
    """Compose a nested ``{datacenter: {cluster: {host: [vm,...]}}}`` map.

    Single REST call each for datacenters, clusters, hosts, vms, then aggregated
    in Python. VMs not bound to a host (templates, disconnected) land under the
    sentinel ``"__unbound__"`` host bucket within their cluster bucket.
    """
    datacenters = vcenter_datacenter.list_(opts, profile=profile)
    clusters = vcenter_cluster.list_(opts, profile=profile)
    hosts = vcenter_host.list_(opts, profile=profile)
    vms = list_(opts, profile=profile)

    host_to_cluster = {h["host"]: h.get("cluster") for h in hosts}
    cluster_to_dc = {c["cluster"]: c.get("datacenter") for c in clusters}

    result = {}
    for dc in datacenters:
        result[dc["datacenter"]] = {"name": dc.get("name"), "clusters": {}}
    for c in clusters:
        bucket = result.setdefault(c.get("datacenter"), {"name": None, "clusters": {}})
        bucket["clusters"].setdefault(c["cluster"], {"name": c.get("name"), "hosts": {}})
    for h in hosts:
        dc_id = cluster_to_dc.get(h.get("cluster"))
        dc_bucket = result.setdefault(dc_id, {"name": None, "clusters": {}})
        cl_bucket = dc_bucket["clusters"].setdefault(h.get("cluster"), {"name": None, "hosts": {}})
        cl_bucket["hosts"].setdefault(h["host"], {"name": h.get("name"), "vms": []})
    for v in vms:
        host = v.get("host")
        cluster = host_to_cluster.get(host)
        dc_id = cluster_to_dc.get(cluster)
        dc_bucket = result.setdefault(dc_id, {"name": None, "clusters": {}})
        cl_bucket = dc_bucket["clusters"].setdefault(cluster, {"name": None, "hosts": {}})
        host_key = host or "__unbound__"
        host_bucket = cl_bucket["hosts"].setdefault(host_key, {"name": None, "vms": []})
        host_bucket["vms"].append(v)
    return result


def summary(opts, profile=None):
    """Aggregate counts from ``list_()``: by_power_state, by_cpu_count, total."""
    vms = list_(opts, profile=profile)
    by_power_state = {}
    by_cpu = {}
    total_memory = 0
    for v in vms:
        ps = v.get("power_state", "UNKNOWN")
        by_power_state[ps] = by_power_state.get(ps, 0) + 1
        cpu = v.get("cpu_count")
        if cpu is not None:
            by_cpu[cpu] = by_cpu.get(cpu, 0) + 1
        mem = v.get("memory_size_MiB")
        if isinstance(mem, int):
            total_memory += mem
    return {
        "total": len(vms),
        "by_power_state": by_power_state,
        "by_cpu_count": by_cpu,
        "total_memory_MiB": total_memory,
    }
