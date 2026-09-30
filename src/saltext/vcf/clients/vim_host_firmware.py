"""ESXi firmware config backup / restore / reset via ``HostFirmwareSystem``.

Port of ``vmware_esxi.backup_config`` / ``restore_config`` /
``reset_config``. Backup downloads the host's config bundle over HTTPS
using the returned URL; restore PUTs a bundle to the host's firmware
upload URL (authenticated with the ESXi credentials from pillar) and
brackets the restore with maintenance mode.
"""

import logging
from pathlib import Path

import requests
from pyVmomi import vim

from saltext.vcf.utils import vim as soap

log = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 600


def _resolve(opts, host, profile=None):
    return soap.resolve_host_system(opts, host, profile=profile)


def _firmware_system(opts, host, profile=None):
    h = _resolve(opts, host, profile=profile)
    fs = h.configManager.firmwareSystem
    if fs is None:
        raise RuntimeError(f"host {host!r} has no firmwareSystem manager")
    return h, fs


def _download(url, verify_ssl):
    resp = requests.get(url, verify=verify_ssl, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.content


def _upload(url, data, opts, profile=None):
    """PUT the bundle bytes to *url*, authenticating with the ESXi credentials.

    The host-issued firmware upload URL requires the ESXi root
    credentials — re-read them from the configured connection block.
    """
    from saltext.vcf.utils import esxi as esxi_conn  # noqa: PLC0415

    conf = esxi_conn.get_config(opts, profile=profile)
    auth = (conf.get("username"), conf.get("password"))
    resp = requests.put(url, data=data, auth=auth, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.status_code


def backup(opts, host, *, cachedir=None, verify_ssl=False, profile=None):
    """Back up the host configuration into *cachedir* (default: minion cache dir).

    Returns ``{host: {"file_name", "url", "sha1"}}``. The exec-module
    wrapper pushes the file to the master with ``cp.push`` when
    requested.
    """
    h, fs = _firmware_system(opts, host, profile=profile)
    url = fs.BackupFirmwareConfiguration().replace("*", h.name)
    file_name = Path(cachedir or "/var/cache/salt/minion") / url.rsplit("/", 1)[-1]
    data = _download(url, verify_ssl)
    file_name.parent.mkdir(parents=True, exist_ok=True)
    file_name.write_bytes(data)
    import hashlib  # noqa: PLC0415

    digest = hashlib.sha1(data, usedforsecurity=False).hexdigest()  # nosec B324
    return {h.name: {"file_name": str(file_name), "url": url, "sha1": digest}}


def restore(opts, host, source_file, *, verify_ssl=False, profile=None):
    """Restore the host configuration from a local file or ``http(s)://`` URL.

    ``salt://`` sources must be cached by the caller (the exec-module
    wrapper handles that with ``cp.cache_file``). The bundle is PUT to
    the host's firmware upload URL and
    ``RestoreFirmwareConfiguration(force=False)`` runs while the host is
    in maintenance mode.
    """
    h, fs = _firmware_system(opts, host, profile=profile)
    url = fs.QueryFirmwareConfigUploadURL().replace("*", h.name)
    if source_file.startswith("http"):
        data = _download(source_file, verify_ssl)
    else:
        data = Path(source_file).read_bytes()
    entered_mm = False
    if not h.runtime.inMaintenanceMode:
        task = h.EnterMaintenanceMode_Task(timeout=60)
        soap.wait_for_task(task)
        entered_mm = True
    try:
        _upload(url, data, opts, profile=profile)
        fs.RestoreFirmwareConfiguration(force=False)
        return {h.name: True}
    except Exception:
        log.exception("restore for host %s failed", h.name)
        raise
    finally:
        if entered_mm:
            task = h.ExitMaintenanceMode_Task(timeout=60)
            soap.wait_for_task(task)


def reset(opts, host, profile=None):
    """Reset the host configuration to factory defaults (in maintenance mode)."""
    h, fs = _firmware_system(opts, host, profile=profile)
    entered_mm = False
    if not h.runtime.inMaintenanceMode:
        task = h.EnterMaintenanceMode_Task(timeout=60)
        soap.wait_for_task(task)
        entered_mm = True
    try:
        fs.ResetFirmwareToFactoryDefaults()
        return {h.name: True}
    finally:
        if entered_mm:
            task = h.ExitMaintenanceMode_Task(timeout=60)
            soap.wait_for_task(task)
