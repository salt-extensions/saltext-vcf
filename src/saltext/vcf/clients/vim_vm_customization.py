"""Guest OS customization specs + apply.

Two surfaces:

* Build a customization spec from kwargs (``linux_spec``, ``windows_spec``)
  for use with :func:`saltext.vcf.clients.vim_vm.clone`.
* Apply a spec to an existing VM via ``CustomizeVM_Task``.

The customization manager can also store named specs server-side; that
surface is exposed via :func:`spec_get`, :func:`spec_create`,
:func:`spec_delete`.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _csmgr(opts, profile=None):
    return soap.content(opts, profile=profile).customizationSpecManager


# ---------------------------------------------------------------------------
# Spec builders (return ``vim.vm.customization.Specification`` objects)
# ---------------------------------------------------------------------------


def linux_spec(
    hostname,
    domain,
    time_zone="UTC",
    hw_clock_utc=True,
    nics=None,
    dns_servers=None,
    dns_search_path=None,
):
    """Build a Linux customization spec.

    *nics* is a list of network adapter dicts:

    .. code-block:: python

        [{"dhcp": True}, {"ip": "10.0.0.5", "subnet": "255.255.255.0", "gateway": ["10.0.0.1"]}]
    """
    identity = vim.vm.customization.LinuxPrep(
        hostName=vim.vm.customization.FixedName(name=hostname),
        domain=domain,
        timeZone=time_zone,
        hwClockUTC=hw_clock_utc,
    )
    return _build_spec(identity, nics, dns_servers, dns_search_path)


def windows_spec(
    hostname,
    workgroup_or_domain,
    *,
    domain_join=False,
    domain_admin=None,
    domain_admin_password=None,
    admin_password=None,
    auto_logon=False,
    auto_logon_count=1,
    license_mode="perServer",
    product_id=None,
    full_name="Administrator",
    org_name="VMware",
    time_zone=85,
    nics=None,
    dns_servers=None,
    dns_search_path=None,
):
    """Build a Windows customization spec.

    *time_zone* is the Microsoft TimeZoneIndex (85 = Pacific).
    """
    identity = vim.vm.customization.Sysprep()
    identity.guiUnattended = vim.vm.customization.GuiUnattended(
        autoLogon=auto_logon,
        autoLogonCount=auto_logon_count,
        timeZone=time_zone,
    )
    if admin_password is not None:
        identity.guiUnattended.password = vim.vm.customization.Password(
            value=admin_password, plainText=True
        )
    identity.userData = vim.vm.customization.UserData(
        fullName=full_name,
        orgName=org_name,
        computerName=vim.vm.customization.FixedName(name=hostname),
        productId=product_id or "",
    )
    if domain_join:
        identity.identification = vim.vm.customization.Identification(
            joinDomain=workgroup_or_domain,
            domainAdmin=domain_admin,
            domainAdminPassword=(
                vim.vm.customization.Password(value=domain_admin_password, plainText=True)
                if domain_admin_password
                else None
            ),
        )
    else:
        identity.identification = vim.vm.customization.Identification(
            joinWorkgroup=workgroup_or_domain
        )
    identity.licenseFilePrintData = vim.vm.customization.LicenseFilePrintData(autoMode=license_mode)
    return _build_spec(identity, nics, dns_servers, dns_search_path)


def _build_spec(identity, nics, dns_servers, dns_search_path):
    global_ip = vim.vm.customization.GlobalIPSettings(
        dnsServerList=list(dns_servers or []),
        dnsSuffixList=list(dns_search_path or []),
    )
    adapter_mappings = []
    for nic in nics or []:
        ip = _ip_for(nic)
        adapter = vim.vm.customization.IPSettings(
            ip=ip,
            subnetMask=nic.get("subnet", ""),
            gateway=list(nic.get("gateway") or []),
            dnsServerList=list(nic.get("dns_servers") or []),
            dnsDomain=nic.get("domain"),
        )
        adapter_mappings.append(vim.vm.customization.AdapterMapping(adapter=adapter))
    return vim.vm.customization.Specification(
        identity=identity,
        globalIPSettings=global_ip,
        nicSettingMap=adapter_mappings,
    )


def _ip_for(nic):
    if nic.get("dhcp"):
        return vim.vm.customization.DhcpIpGenerator()
    if nic.get("ip"):
        return vim.vm.customization.FixedIp(ipAddress=nic["ip"])
    raise ValueError(f"nic spec must include 'dhcp' or 'ip': {nic!r}")


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply(opts, vm_id_or_name, spec, profile=None):
    """Apply *spec* (built via :func:`linux_spec` / :func:`windows_spec`) to a VM."""
    from saltext.vcf.clients.vim_vm import _vm  # avoid circular at import time

    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.CustomizeVM_Task(spec=spec)
    return task._moId  # noqa: SLF001


def set_ip_info(
    opts,
    vm_id_or_name,
    *,
    ip,
    subnet,
    gateway,
    dns=None,
    domain=None,
    guest_os=None,
    profile=None,
):
    """Set static IP config on a powered-off VM (``vmware_vm.set_ip_info`` parity).

    Builds a minimal customization spec — ``LinuxPrep`` for Linux guests,
    bare ``Sysprep`` for Windows — with one NIC mapping (ip, subnet mask,
    gateway, DNS servers) plus global DNS settings. The VM must be
    powered off; the guest OS is sniffed from ``guestFullName`` or taken
    from *guest_os* for freshly-imported VMs.
    """
    from saltext.vcf.clients.vim_vm import _vm  # avoid circular at import time

    vm = _vm(opts, vm_id_or_name, profile=profile)
    if vm.runtime.powerState == "poweredOn":
        raise RuntimeError("VM must be powered off before IP customization")
    vm_os = (
        (getattr(vm.summary.guest, "guestFullName", None) or "").lower()
        or (guest_os or "").lower()
    )
    if not vm_os:
        raise ValueError("guestFullName is empty AND guest_os was not passed")
    if "linux" in vm_os:
        identity = vim.vm.customization.LinuxPrep(
            hostName=vim.vm.customization.FixedName(name=vm.name),
            domain=domain or "",
        )
    elif "windows" in vm_os:
        identity = vim.vm.customization.Sysprep()
    else:
        raise ValueError("Unsupported OS for IP customization")
    nics = [
        d for d in vm.config.hardware.device or [] if isinstance(d, vim.vm.device.VirtualEthernetCard)
    ]
    if len(nics) > 1:
        raise RuntimeError("Only a single NIC is supported for IP customization")
    ip_settings = vim.vm.customization.IPSettings(
        ip=vim.vm.customization.FixedIp(ipAddress=ip),
        subnetMask=subnet,
        gateway=[gateway],
        dnsServerList=list(dns or []),
        dnsDomain=domain,
    )
    global_ip = vim.vm.customization.GlobalIPSettings(
        dnsServerList=list(dns or []),
        dnsSuffixList=[domain] if domain else [],
    )
    spec = vim.vm.customization.Specification(
        identity=identity,
        globalIPSettings=global_ip,
        nicSettingMap=[vim.vm.customization.AdapterMapping(adapter=ip_settings)],
    )
    task = vm.CustomizeVM_Task(spec=spec)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Server-side named specs
# ---------------------------------------------------------------------------


def spec_list(opts, profile=None):
    """Return the names of every saved customization spec on the vCenter."""
    return [info.name for info in (_csmgr(opts, profile=profile).info or [])]


def spec_get(opts, name, profile=None):
    """Return a saved spec by name (as a ``vim.vm.customization.Specification``)."""
    mgr = _csmgr(opts, profile=profile)
    item = mgr.GetCustomizationSpec(name=name)
    return item.spec


def spec_create(opts, name, description, spec, profile=None):
    """Save *spec* under *name* on the vCenter."""
    mgr = _csmgr(opts, profile=profile)
    item = vim.CustomizationSpecItem(
        info=vim.CustomizationSpecInfo(
            name=name, description=description, type="Lin"  # Lin/Win — vCenter accepts both
        ),
        spec=spec,
    )
    mgr.CreateCustomizationSpec(item=item)


def spec_delete(opts, name, profile=None):
    _csmgr(opts, profile=profile).DeleteCustomizationSpec(name=name)
