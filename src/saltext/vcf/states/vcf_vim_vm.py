"""
State module for VM lifecycle via SOAP.

Idempotent-on-existence wrappers over the ``vcf_vim_vm``,
``vcf_vim_vm_disk``, ``vcf_vim_vm_nic``, ``vcf_vim_vm_features``, and
``vcf_vim_vm_power`` execution modules.

The ``present`` state is a shortest-path VM creator: create + attach
disks + attach NICs + set features (VHV, firmware) in one shot.  If
the VM already exists, no changes are made — drift reconciliation is
out of scope; use the underlying per-device exec modules for that.

Example — a nested ESXi hypervisor VM::

    esxi-nested-01:
      vcf_vim_vm.present:
        - name: esxi-nested-01
        - host: 192.168.0.24
        - datastore: datastore-ssd-4tb
        - folder: vm
        - cpu_count: 4
        - memory_mb: 16384
        - guest_id: vmkernel8Guest
        - firmware: efi
        - nested_hv: true
        - disks:
            - size_gb: 32
            - size_gb: 40
            - size_gb: 100
        - nics:
            - network: nested-lab
"""

__virtualname__ = "vcf_vim_vm"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(
    name,
    host,
    datastore,
    folder="vm",
    cpu_count=1,
    memory_mb=1024,
    guest_id="otherGuest64",
    firmware=None,
    nested_hv=None,
    efi_secure_boot=None,
    disks=None,
    nics=None,
    annotation="",
    profile=None,
):
    """Ensure a VM exists with the given hardware layout.

    On first apply: create the VM, attach ``disks`` (list of dicts with
    ``size_gb``, optional ``thin_provisioned``), attach ``nics`` (list
    of dicts with ``network`` — the port-group name), and apply
    feature toggles.

    On subsequent applies: if the VM already exists (by name), report
    "already present" and make no changes.  Deeper drift reconciliation
    is out of scope for this state — use per-device exec modules.
    """
    ret = _ret(name)
    # Existence probe (list_ + name match).  vcf_vim_vm has no
    # get_or_none primitive, so use the exec module's advanced-settings
    # fetch as a cheap existence check and catch LookupError.
    try:
        __salt__["vcf_vim_vm.get_advanced_settings"](name, profile=profile)
        ret["comment"] = f"VM {name!r} already present on {host}."
        return ret
    except LookupError:
        pass

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = (
            f"Would create VM {name!r} on {host} with {cpu_count} vCPU, "
            f"{memory_mb} MB RAM, {len(disks or [])} disk(s), "
            f"{len(nics or [])} NIC(s)."
        )
        ret["changes"] = {"new": name}
        return ret

    __salt__["vcf_vim_vm.create"](
        name,
        folder=folder,
        datastore=datastore,
        cpu_count=cpu_count,
        memory_mb=memory_mb,
        guest_id=guest_id,
        host=host,
        annotation=annotation,
        profile=profile,
    )
    changes = {"created": name, "disks": [], "nics": [], "features": {}}
    for disk in disks or []:
        __salt__["vcf_vim_vm_disk.add"](
            name,
            size_gb=int(disk["size_gb"]),
            thin=disk.get("thin", True),
            profile=profile,
        )
        changes["disks"].append(disk["size_gb"])
    for nic in nics or []:
        __salt__["vcf_vim_vm_nic.add"](
            name,
            network=nic["network"],
            nic_type=nic.get("nic_type", "vmxnet3"),
            profile=profile,
        )
        changes["nics"].append(nic["network"])
    features_kwargs = {}
    if firmware is not None:
        features_kwargs["firmware"] = firmware
    if nested_hv is not None:
        features_kwargs["nested_hv"] = nested_hv
    if efi_secure_boot is not None:
        features_kwargs["efi_secure_boot"] = efi_secure_boot
    if features_kwargs:
        __salt__["vcf_vim_vm_features.set_features"](name, profile=profile, **features_kwargs)
        changes["features"] = features_kwargs
    ret["changes"] = changes
    ret["comment"] = f"Created VM {name!r} on {host}."
    return ret


def absent(name, profile=None):
    """Ensure the VM *name* is not present.

    Powers it off first if running; ``vim_vm.destroy`` requires a
    powered-off VM.
    """
    ret = _ret(name)
    try:
        __salt__["vcf_vim_vm.get_advanced_settings"](name, profile=profile)
    except LookupError:
        ret["comment"] = f"VM {name!r} already absent."
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Would destroy VM {name!r}."
        ret["changes"] = {"old": name}
        return ret

    # Best-effort power-off; ignore state errors so a stopped VM still
    # deletes cleanly.
    try:
        __salt__["vcf_vim_vm_power.power_off"](name, profile=profile)
    except Exception:  # pylint: disable=broad-except
        pass
    __salt__["vcf_vim_vm.destroy"](name, profile=profile)
    ret["changes"] = {"destroyed": name}
    ret["comment"] = f"Destroyed VM {name!r}."
    return ret


def powered_on(name, profile=None):
    """Ensure VM *name* is powered on."""
    ret = _ret(name)
    state = __salt__["vcf_vim_vm_power.get_power_state"](name, profile=profile)
    if state == "poweredOn":
        ret["comment"] = f"VM {name!r} already powered on."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Would power on VM {name!r} (currently {state})."
        return ret
    __salt__["vcf_vim_vm_power.power_on"](name, profile=profile)
    ret["changes"] = {"power": {"old": state, "new": "poweredOn"}}
    ret["comment"] = f"Powered on VM {name!r}."
    return ret


def powered_off(name, profile=None):
    """Ensure VM *name* is powered off."""
    ret = _ret(name)
    state = __salt__["vcf_vim_vm_power.get_power_state"](name, profile=profile)
    if state == "poweredOff":
        ret["comment"] = f"VM {name!r} already powered off."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Would power off VM {name!r} (currently {state})."
        return ret
    __salt__["vcf_vim_vm_power.power_off"](name, profile=profile)
    ret["changes"] = {"power": {"old": state, "new": "poweredOff"}}
    ret["comment"] = f"Powered off VM {name!r}."
    return ret
