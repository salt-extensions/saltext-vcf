"""ESXi host lifecycle, power state, capability and info aggregation via SOAP.

Ported from ``vmware_esxi`` / ``vmware_vsphere`` in ``saltext.vmware``:

* ``connect`` / ``disconnect`` / ``remove`` / ``move`` / ``add`` — host
  membership in vCenter (``ReconnectHost_Task``, ``DisconnectHost_Task``,
  ``Destroy_Task``, ``ClusterComputeResource.MoveInto_Task``,
  ``ClusterComputeResource.AddHost_Task``).
* ``power_state`` — reboot / shutdown / standby / power-on
  (``RebootHost_Task``, ``ShutdownHost_Task``,
  ``PowerDownHostToStandBy_Task``, ``PowerUpHostFromStandBy_Task``).
* ``capabilities`` — ``HostSystem.capability`` dump.
* ``info`` — the ``vmware_esxi.get`` config aggregator with
  ``key``/``default``/``delimiter`` traversal.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _camel_to_snake(name):
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _resolve(opts, host_id_or_name, profile=None):
    return soap.resolve_host_system(opts, host_id_or_name, profile=profile)


# ---------------------------------------------------------------------------
# Lifecycle: reconnect / disconnect / destroy / move / add
# ---------------------------------------------------------------------------


def connection_state(opts, host, profile=None):
    """Return the host's current vCenter connection state."""
    return str(_resolve(opts, host, profile=profile).summary.runtime.connectionState)


def reconnect(opts, host, profile=None):
    """Reconnect a disconnected host. Returns the resulting connection state."""
    h = _resolve(opts, host, profile=profile)
    if h.summary.runtime.connectionState == "connected":
        return h.summary.runtime.connectionState
    task = h.ReconnectHost_Task()
    ret = soap.wait_for_task(task)
    return str(ret.summary.runtime.connectionState)


def disconnect(opts, host, profile=None):
    """Disconnect a host from vCenter. Returns the resulting connection state."""
    h = _resolve(opts, host, profile=profile)
    if h.summary.runtime.connectionState == "disconnected":
        return h.summary.runtime.connectionState
    task = h.DisconnectHost_Task()
    ret = soap.wait_for_task(task)
    return str(ret.summary.runtime.connectionState)


def destroy(opts, host, profile=None):
    """Remove the host from vCenter inventory. Returns task moId."""
    h = _resolve(opts, host, profile=profile)
    task = h.Destroy_Task()
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def _find_cluster(opts, cluster, profile=None):
    """Locate a ``vim.ClusterComputeResource`` by MoID or name (no datacenter scoping)."""
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.ClusterComputeResource], True
    )
    try:
        for entity in container.view:
            if cluster in (entity._moId, entity.name):  # noqa: SLF001
                return entity
    finally:
        container.Destroy()
    raise LookupError(f"cluster {cluster!r} not found")


def move(opts, host, cluster, profile=None):
    """Move *host* into *cluster* (same datacenter enforced). Returns a status string."""
    h = _resolve(opts, host, profile=profile)
    target = _find_cluster(opts, cluster, profile=profile)
    cluster_dc = getattr(target.parent, "parent", None)
    host_dc = None
    node = h
    while node is not None:
        if isinstance(node, vim.Datacenter):
            host_dc = node
            break
        node = getattr(node, "parent", None)
    if host_dc is not None and cluster_dc is not None and host_dc._moId != cluster_dc._moId:  # noqa: SLF001
        raise RuntimeError("cluster has to be in the same datacenter as the host")
    task = target.MoveInto_Task([h])
    soap.wait_for_task(task)
    return f"moved {h.name} to {target.name}"


def add(
    opts,
    host,
    root_user,
    password,
    cluster=None,
    datacenter=None,
    *,
    verify_host_cert=False,
    connect=True,
    profile=None,
):
    """Add a bare ESXi host to vCenter under *cluster*.

    *host* is the ESXi hostname/IP. The SSL thumbprint is fetched live
    (reuse :func:`saltext.vcf.clients.vim_host_ssl_thumbprint.fetch`);
    with ``verify_host_cert=True`` a CA-signed, hostname-matching cert is
    required by the TLS layer before the thumbprint is offered.
    """
    from saltext.vcf.clients.vim_host_ssl_thumbprint import fetch  # noqa: PLC0415

    content = soap.content(opts, profile=profile)
    if not (cluster and datacenter):
        raise ValueError("both datacenter and cluster are required to add a host")
    dc = None
    for d in content.rootFolder.childEntity:
        if isinstance(d, vim.Datacenter) and datacenter in (d._moId, d.name):  # noqa: SLF001
            dc = d
            break
    if dc is None:
        raise LookupError(f"datacenter {datacenter!r} not found")
    target = None
    for entity in dc.hostFolder.childEntity:
        if cluster in (getattr(entity, "_moId", None), getattr(entity, "name", None)):
            target = entity
            break
    if target is None:
        raise LookupError(f"cluster {cluster!r} not found in datacenter {datacenter!r}")
    spec = vim.host.ConnectSpec(
        hostName=host,
        userName=root_user,
        password=password,
        sslThumbprint=fetch(host),
    )
    task = target.AddHost_Task(spec, bool(connect))
    ret = soap.wait_for_task(task)
    return str(ret.summary.runtime.connectionState)


# ---------------------------------------------------------------------------
# Power state
# ---------------------------------------------------------------------------


def power_state(opts, host, state, *, timeout=600, force=True, profile=None):
    """Transition the host power state: ``reboot`` | ``shutdown`` | ``standby`` | ``poweron``.

    Returns a ``{"task": moId}`` for async transitions or
    ``{"already": ...}`` no-op dicts when the desired state already
    holds. *standby* uses ``PowerDownHostToStandBy_Task(timeoutSec,
    evacuatePoweredOffVms)`` and *poweron*
    ``PowerUpHostFromStandBy_Task(timeoutSec)``. ``runtime.standbyMode``
    is ``none`` / ``entering`` / ``entered`` / ``exiting`` / ``unknown``.
    """
    h = _resolve(opts, host, profile=profile)
    if state == "reboot":
        task = h.RebootHost_Task(force)
        return {"task": task._moId}  # noqa: SLF001
    if state == "shutdown":
        task = h.ShutdownHost_Task(force)
        return {"task": task._moId}  # noqa: SLF001
    in_standby = h.runtime.standbyMode in ("entered", "entering")
    if state == "standby":
        if in_standby:
            return {"already": "standby"}
        task = h.PowerDownHostToStandBy_Task(int(timeout), bool(force))
        return {"task": task._moId}  # noqa: SLF001
    if state == "poweron":
        if not in_standby:
            return {"already": "powered on"}
        task = h.PowerUpHostFromStandBy_Task(int(timeout))
        return {"task": task._moId}  # noqa: SLF001
    raise ValueError(f"state must be one of reboot, shutdown, standby, poweron (got {state!r})")


# ---------------------------------------------------------------------------
# Capability + info aggregator
# ---------------------------------------------------------------------------


def capabilities(opts, host, profile=None):
    """Return the host's ``HostCapability`` attribs as a snake_case dict."""
    h = _resolve(opts, host, profile=profile)
    out = {}
    for attrib in dir(h.capability):
        if attrib.startswith("_") or attrib.lower() == "array":
            continue
        val = getattr(h.capability, attrib)
        if isinstance(val, list):
            val = list(val)
        out[_camel_to_snake(attrib)] = val
    return out


def _host_info_dict(h):
    ret = {"vsan": {}}
    vsan_manager = h.configManager.vsanSystem
    if vsan_manager is not None:
        try:
            vsan = vsan_manager.QueryHostStatus()
            ret["vsan"] = {
                "cluster_uuid": vsan.uuid,
                "node_uuid": vsan.nodeUuid,
                "health": vsan.health,
            }
        except Exception:  # pylint: disable=broad-except
            ret["vsan"] = {}
    ret["datastores"] = {}
    for store in h.datastore or []:
        ret["datastores"][store.name] = {
            "capacity": store.summary.capacity,
            "free_space": store.summary.freeSpace,
        }
    ret["nics"] = {}
    for nic in ((h.config.network.vnic if h.config and h.config.network else []) or []):
        ret["nics"][nic.device] = {
            "ip_address": nic.spec.ip.ipAddress,
            "subnet_mask": nic.spec.ip.subnetMask,
            "mac": nic.spec.mac,
            "mtu": nic.spec.mtu,
        }
    ret["cpu_model"] = h.summary.hardware.cpuModel
    ret["num_cpu_cores"] = h.summary.hardware.numCpuCores
    ret["num_cpu_pkgs"] = h.summary.hardware.numCpuPkgs
    ret["num_cpu_threads"] = h.summary.hardware.numCpuThreads
    ret["memory_size"] = h.summary.hardware.memorySize
    ret["overall_memory_usage"] = h.summary.quickStats.overallMemoryUsage
    ret["product_name"] = h.config.product.name
    ret["product_version"] = h.config.product.version
    ret["product_build"] = h.config.product.build
    ret["product_os_type"] = h.config.product.osType
    ret["host_name"] = h.summary.config.name
    ret["system_vendor"] = h.hardware.systemInfo.vendor
    ret["system_model"] = h.hardware.systemInfo.model
    ret["bios_release_date"] = h.hardware.biosInfo.releaseDate
    ret["bios_release_version"] = h.hardware.biosInfo.biosVersion
    ret["uptime"] = h.summary.quickStats.uptime
    ret["in_maintenance_mode"] = h.runtime.inMaintenanceMode
    ret["system_uuid"] = h.hardware.systemInfo.uuid
    for info in (h.hardware.systemInfo.otherIdentifyingInfo or []):
        ret[_camel_to_snake(info.identifierType.key)] = info.identifierValue
    return ret


def info(opts, host, *, key=None, default="", delimiter=":", profile=None):
    """Return the composed per-host info dict (or a single traversed *key*).

    *key* supports nested traversal with *delimiter* (e.g. ``vsan:health``),
    returning *default* when missing — the ``vmware_esxi.get`` semantics.
    """
    h = _resolve(opts, host, profile=profile)
    ret = _host_info_dict(h)
    if key:
        return _traverse(ret, key, default, delimiter)
    return ret


def _traverse(data, key, default, delimiter):
    node = data
    for part in key.split(delimiter):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node
