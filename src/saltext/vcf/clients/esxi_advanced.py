"""ESXi advanced system settings via SOAP/pyVmomi."""

from pyVmomi import vim
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from saltext.vcf.utils import esxi


def list_(opts, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    options = host.configManager.advancedOption.QueryOptions()
    return {opt.key: opt.value for opt in (options or [])}


def get(opts, key, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    options = host.configManager.advancedOption.QueryOptions(name=key)
    if not options:
        raise KeyError(f"Advanced setting {key!r} not found")
    return options[0].value


def get_or_none(opts, key, profile=None):
    try:
        return get(opts, key, profile=profile)
    except (KeyError, vim.fault.VimFault, vmodl.MethodFault):
        return None


def set_value(opts, key, value, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.advancedOption.UpdateValues(
        changedValue=[vim.option.OptionValue(key=key, value=value)]
    )
    return {"key": key, "value": value}
