"""VM NIC lifecycle via SOAP ``VirtualMachine.ReconfigVM_Task``."""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap

_NIC_TYPES = {
    "vmxnet3": vim.vm.device.VirtualVmxnet3,
    "vmxnet2": vim.vm.device.VirtualVmxnet2,
    "e1000": vim.vm.device.VirtualE1000,
    "e1000e": vim.vm.device.VirtualE1000e,
    "pcnet32": vim.vm.device.VirtualPCNet32,
    "sriov": vim.vm.device.VirtualSriovEthernetCard,
}


def _vm(opts, vm_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    try:
        for vm in container.view:
            if vm_id_or_name in (vm._moId, vm.name):  # noqa: SLF001
                return vm
    finally:
        container.Destroy()
    raise LookupError(f"VM {vm_id_or_name!r} not found")


def _find_network(opts, name_or_id, profile=None):
    """Locate a ``vim.Network`` by MOID or name.

    Standard port groups surface as ``vim.Network`` in the datacenter's
    ``networkFolder`` on both ESXi and vCenter.  Callers that pass a
    port-group name get resolved to the underlying MOID here.
    """
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True)
    try:
        for net in container.view:
            if name_or_id in (net._moId, net.name):  # noqa: SLF001
                return net
    finally:
        container.Destroy()
    raise LookupError(f"network {name_or_id!r} not found")


def list_(opts, vm_id_or_name, profile=None):
    """Return every Ethernet device on the VM as a list of dicts."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    out = []
    for dev in vm.config.hardware.device or []:
        if not isinstance(dev, vim.vm.device.VirtualEthernetCard):
            continue
        backing = dev.backing
        backing_kind = type(backing).__name__ if backing else None
        network = getattr(backing, "network", None)
        portgroup_key = getattr(getattr(backing, "port", None), "portgroupKey", None)
        out.append(
            {
                "key": dev.key,
                "label": dev.deviceInfo.label,
                "summary": dev.deviceInfo.summary,
                "mac_address": dev.macAddress,
                "mac_type": dev.addressType,
                "device_type": type(dev).__name__,
                "connected": dev.connectable.connected if dev.connectable else None,
                "start_connected": (dev.connectable.startConnected if dev.connectable else None),
                "backing_kind": backing_kind,
                "network_moid": network._moId if network else None,  # noqa: SLF001
                "portgroup_key": portgroup_key,
            }
        )
    return out


def add(
    opts,
    vm_id_or_name,
    *,
    nic_type="vmxnet3",
    network=None,
    network_moid=None,
    portgroup_key=None,
    dvs_uuid=None,
    mac_address=None,
    start_connected=True,
    profile=None,
):
    """Add a new NIC.

    Backing options:

    * *network* — legacy port-group name (looked up via ``vim.Network``).
      Convenience for callers who only know the port-group label —
      typical for standalone-ESXi and single-vSwitch setups.
    * *network_moid* — legacy port group by MOID (bypasses the lookup).
    * *portgroup_key* + *dvs_uuid* — distributed port group.
    """
    # Port groups on a standalone-ESXi standard vSwitch that only
    # carry VMkernel traffic (no VMs) are NOT advertised as
    # ``vim.Network`` MOs.  ``_find_network`` will miss them.  Fall
    # back to a ``deviceName``-only backing (no ``network`` MO
    # reference) — ESXi resolves the port group by name at attach
    # time.  Works for both regular port groups and vmk-only ones.
    network_obj = None
    device_name = None
    if network and not network_moid:
        try:
            network_obj = _find_network(opts, network, profile=profile)
            network_moid = network_obj._moId  # noqa: SLF001
        except LookupError:
            device_name = network
    if (
        not network_obj
        and not network_moid
        and not device_name
        and not (portgroup_key and dvs_uuid)
    ):
        raise ValueError("provide network OR network_moid OR (portgroup_key AND dvs_uuid)")
    nic_cls = _NIC_TYPES.get(nic_type.lower())
    if nic_cls is None:
        raise ValueError(f"unknown nic_type {nic_type!r}; valid: {sorted(_NIC_TYPES)}")
    nic = nic_cls(key=-1)
    if portgroup_key and dvs_uuid:
        backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        backing.port = vim.dvs.PortConnection(portgroupKey=portgroup_key, switchUuid=dvs_uuid)
    elif device_name is not None:
        # deviceName-only path: ESXi resolves by name.  Used for
        # port groups that don't have a vim.Network MO (e.g.
        # vmk-only port groups on standalone ESXi).
        backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        backing.deviceName = device_name
    else:
        # NetworkBackingInfo needs the actual vim.Network managed
        # object reference, not a synthesised one — ESXi rejects a
        # bare-MoID Network with "Invalid configuration for device".
        if network_obj is None:
            network_obj = _find_network(opts, network_moid, profile=profile)
        backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        backing.network = network_obj
        try:
            backing.deviceName = network_obj.name
        except AttributeError:
            backing.deviceName = ""
    nic.backing = backing
    if mac_address:
        nic.macAddress = mac_address
        nic.addressType = "manual"
    else:
        # 'generated' works on both ESXi and vCenter; 'assigned' is
        # vCenter-only (VC pre-computes the MAC and hands it back).
        # Standalone ESXi rejects 'assigned' with "Invalid
        # configuration for device 0".
        nic.addressType = "generated"
    nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
        startConnected=start_connected, allowGuestControl=True
    )
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="add", device=nic)]
    )
    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def update_backing(
    opts,
    vm_id_or_name,
    nic_key,
    *,
    network_moid=None,
    portgroup_key=None,
    dvs_uuid=None,
    profile=None,
):
    """Reattach an existing NIC to a different network / port group."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    nic = _find_nic(vm, nic_key)
    if portgroup_key and dvs_uuid:
        backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        backing.port = vim.dvs.PortConnection(portgroupKey=portgroup_key, switchUuid=dvs_uuid)
    elif network_moid:
        backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        backing.network = vim.Network(network_moid, None)
        backing.deviceName = ""
    else:
        raise ValueError("provide network_moid OR (portgroup_key AND dvs_uuid)")
    nic.backing = backing
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="edit", device=nic)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def set_connected(opts, vm_id_or_name, nic_key, connected, profile=None):
    """Hot-toggle a NIC's connected state."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    nic = _find_nic(vm, nic_key)
    if nic.connectable is None:
        nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic.connectable.connected = bool(connected)
    nic.connectable.startConnected = bool(connected)
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="edit", device=nic)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def remove(opts, vm_id_or_name, nic_key, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    nic = _find_nic(vm, nic_key)
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="remove", device=nic)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def _find_nic(vm, key):
    for dev in vm.config.hardware.device or []:
        if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.key == int(key):
            return dev
    raise LookupError(f"NIC key {key!r} not found on VM {vm.name!r}")
