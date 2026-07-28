"""Client for DVS Network I/O Control (NIOC) via SOAP/pyVmomi.

Covers the switch-wide NIOC enable/disable toggle
(``EnableNetworkResourceManagement``) on a Distributed Virtual Switch.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _dvs(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.DistributedVirtualSwitch], True
    )
    try:
        for dvs in container.view:
            if name_or_id in (dvs._moId, dvs.name, dvs.uuid):  # noqa: SLF001
                return dvs
    finally:
        container.Destroy()
    raise LookupError(f"DVS {name_or_id!r} not found")


def nioc_get(opts, dvs_name_or_id, profile=None):
    """Return whether Network I/O Control is enabled on the DVS."""
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    return bool(dvs.config.networkResourceManagementEnabled)


def nioc_set(opts, dvs_name_or_id, enabled, profile=None):
    """Enable or disable Network I/O Control on the DVS."""
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    dvs.EnableNetworkResourceManagement(enable=bool(enabled))
