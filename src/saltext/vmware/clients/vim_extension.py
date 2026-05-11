"""vCenter ExtensionManager (SOAP) — plugin/extension registration.

REST has no equivalent. Used to register external services (including
Salt itself, when running as a vCenter extension) so they show up in the
vCenter UI plugin list and can publish events / consume privileges.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def list_(opts, profile=None):
    """Return all registered extensions, as a list of dicts."""
    em = soap.extension_manager(opts, profile=profile)
    return [_extension_to_dict(e) for e in em.extensionList]


def get(opts, key, profile=None):
    """Return the extension whose ``key`` matches, or None."""
    em = soap.extension_manager(opts, profile=profile)
    ext = em.FindExtension(extensionKey=key)
    return _extension_to_dict(ext) if ext is not None else None


def get_or_none(opts, key, profile=None):
    return get(opts, key, profile=profile)


def register(opts, key, version, description, company, profile=None, **fields):
    """Register a new extension with the given *key*.

    *fields* may include ``server`` (a list of dicts with ``url``,
    ``description``, ``adminEmail``), ``client`` (list with ``url``,
    ``description``, ``version``, ``type``), and other Extension subfields.
    """
    em = soap.extension_manager(opts, profile=profile)
    ext = vim.Extension()
    ext.key = key
    ext.version = version
    ext.description = vim.Description()
    ext.description.label = description
    ext.description.summary = description
    ext.company = company
    if "server" in fields:
        ext.server = fields["server"]
    if "client" in fields:
        ext.client = fields["client"]
    em.RegisterExtension(extension=ext)
    return key


def update(opts, key, version=None, description=None, profile=None, **fields):
    """Update an existing extension's registration."""
    em = soap.extension_manager(opts, profile=profile)
    ext = em.FindExtension(extensionKey=key)
    if ext is None:
        raise LookupError(f"extension {key!r} is not registered")
    if version is not None:
        ext.version = version
    if description is not None:
        ext.description.label = description
        ext.description.summary = description
    for attr, value in fields.items():
        setattr(ext, attr, value)
    em.UpdateExtension(extension=ext)


def unregister(opts, key, profile=None):
    em = soap.extension_manager(opts, profile=profile)
    em.UnregisterExtension(extensionKey=key)


def _extension_to_dict(ext):
    return {
        "key": ext.key,
        "version": ext.version,
        "company": ext.company,
        "description": ext.description.label if ext.description else None,
        "last_heartbeat_time": (
            ext.lastHeartbeatTime.isoformat() if ext.lastHeartbeatTime else None
        ),
        "server_count": len(ext.server or []),
        "client_count": len(ext.client or []),
    }
