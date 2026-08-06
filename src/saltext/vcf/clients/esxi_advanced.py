"""ESXi advanced system settings via SOAP/pyVmomi."""

from pyVmomi import vim
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from saltext.vcf.utils import esxi


def list_(opts, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    options = host.configManager.advancedOption.QueryOptions()
    return {opt.key: opt.value for opt in (options or [])}


def get(opts, key, profile=None):
    """Return ``{"key": <name>, "value": <current>}``.

    Consistent shape with :func:`set_value` — callers who only need the
    value should ``get(...)["value"]``.  ``vcf_esxi_advanced.setting``
    (the state module) already expects this dict shape.
    """
    host = esxi.get_host_system(opts, profile=profile)
    options = host.configManager.advancedOption.QueryOptions(name=key)
    if not options:
        raise KeyError(f"Advanced setting {key!r} not found")
    return {"key": key, "value": options[0].value}


def get_or_none(opts, key, profile=None):
    try:
        return get(opts, key, profile=profile)
    except (KeyError, vim.fault.VimFault, vmodl.MethodFault):
        return None


def set_value(opts, key, value, profile=None):
    """Set an ESXi advanced setting.

    Reuses the ``OptionValue`` object returned by ``QueryOptions`` (mutating
    its ``.value``) rather than constructing a fresh one from a bare Python
    value — some settings are typed ``xsd:long`` server-side, and a
    freshly-built ``OptionValue`` from a plain Python ``int`` serializes as
    ``xsd:int``, which the host rejects with
    ``vmodl.fault.InvalidArgument(invalidProperty='value')``. See
    :func:`saltext.vcf.clients.vcenter_advanced_option.advanced_set` for the
    vCenter-side counterpart of this same fix.
    """
    host = esxi.get_host_system(opts, profile=profile)
    mgr = host.configManager.advancedOption
    existing = mgr.QueryOptions(name=key)
    if existing:
        opt = existing[0]
        opt.value = value
    else:
        opt = vim.option.OptionValue(key=key, value=value)
    mgr.UpdateValues(changedValue=[opt])
    return {"key": key, "value": value}
