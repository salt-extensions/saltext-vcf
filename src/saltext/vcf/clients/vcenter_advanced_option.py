"""Client for vCenter Server's own advanced settings (``content.setting``) via SOAP/pyVmomi.

Counterpart to :mod:`vim_host_config`'s ``advanced_*`` functions, but scoped
to the connected vCenter Server itself (``config.vpxd.*`` keys) rather than
a managed ``HostSystem``.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def advanced_get(opts, key=None, profile=None):
    """Return vCenter Server advanced settings.

    When *key* is provided, returns the current value, or ``None`` if the
    option has never been set. ``QueryOptions`` raises
    ``vim.fault.InvalidName`` (rather than returning an empty list) for a
    key that's never been touched on this vCenter Server — that's a normal
    "not set yet" state, not an error, since :func:`advanced_set` can still
    create it.

    When *key* is omitted, returns a ``{key: value}`` dict of every setting
    currently known to vCenter.
    """
    option_mgr = soap.content(opts, profile=profile).setting
    if not key:
        return {s.key: s.value for s in (option_mgr.setting or [])}
    try:
        settings = option_mgr.QueryOptions(name=key)
    except vim.fault.InvalidName:
        return None
    return settings[0].value if settings else None


def advanced_set(opts, key, value, profile=None):
    """Set a single vCenter Server advanced setting."""
    option_mgr = soap.content(opts, profile=profile).setting
    opt = vim.option.OptionValue(key=key, value=value)
    option_mgr.UpdateOptions(changedValue=[opt])
