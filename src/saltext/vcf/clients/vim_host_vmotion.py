"""ESXi vMotion interface management via ``HostVMotionSystem``.

Port of ``vmware_esxi.get_vmotion_enabled`` / ``vmotion_enable`` /
``vmotion_disable``. The vMotion interface is the VMkernel NIC selected
for the ``vmotion`` net-stack (``netConfig.selectedVnic``).
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _resolve(opts, host, profile=None):
    return soap.resolve_host_system(opts, host, profile=profile)


def _vmotion_system(opts, host, profile=None):
    h = _resolve(opts, host, profile=profile)
    vmotion = h.configManager.vmotionSystem
    if vmotion is None:
        raise RuntimeError(f"host {host!r} has no vmotionSystem manager")
    return h, vmotion


def get_enabled(opts, host, profile=None):
    """Return ``{"enabled": bool, "device": str|None}`` for the vMotion vNIC.

    The currently selected VMkernel NIC is exposed by
    ``HostVMotionSystem.NetConfig.selectedVnic`` (a ``vim.host.VirtualNic``);
    ``candidateVnic`` lists every VMkernel NIC.
    """
    _h, vmotion = _vmotion_system(opts, host, profile=profile)
    net_config = getattr(vmotion.config, "netConfig", None)
    selected = getattr(net_config, "selectedVnic", None) if net_config is not None else None
    device = getattr(selected, "device", None) if selected is not None else None
    return {"enabled": bool(selected), "device": device}


def enable(opts, host, device="vmk0", profile=None):
    """Select *device* as the VMkernel NIC used for vMotion."""
    _h, vmotion = _vmotion_system(opts, host, profile=profile)
    vmotion.SelectVnic(device=device)
    return {"enabled": True, "device": device}


def disable(opts, host, profile=None):
    """Deselect the vMotion VMkernel NIC."""
    _h, vmotion = _vmotion_system(opts, host, profile=profile)
    current = get_enabled(opts, host, profile=profile)
    if not current["enabled"]:
        return {"enabled": False, "device": None}
    vmotion.DeselectVnic()
    return {"enabled": False, "device": None}
