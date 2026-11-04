import json
import logging
import os

from saltext.vcf.clients.ops_patch_orchestrator import OpsPatchOrchestrator
from saltext.vcf.clients.ops_patch_provider import OpsPatchProvider
from saltext.vcf.utils.config import as_bool
from saltext.vcf.utils.config import as_int
from saltext.vcf.utils.config import get_ops_credentials
from saltext.vcf.utils.config import get_section

log = logging.getLogger(__name__)
__virtualname__ = "vcf_ops_patch"


def __virtual__():
    return __virtualname__


def _connection(overrides=None):
    creds = get_ops_credentials(globals().get("__salt__", {}), overrides or {})

    protocol = str(creds.get("protocol") or "https").strip().lower()
    if protocol not in ("http", "https"):
        protocol = "https"

    host = creds.get("host")
    if not host or str(host).strip() in ("**********", "None", ""):
        # Let the provider/client fail clearly instead of constructing **********://...
        raise ValueError(
            "Missing or masked ops.host. Pass host explicitly in SLS/module args or fix pillar rendering."
        )

    return {
        "host": host,
        "username": creds.get("username"),
        "password": creds.get("password"),
        "protocol": protocol,
        "port": as_int(creds.get("port"), 443),
        "verify_ssl": as_bool(creds.get("verify_ssl"), False),
        "timeout": as_int(creds.get("timeout"), 300),
    }


def _provider(**kwargs):
    return OpsPatchProvider(**_connection(kwargs), logger=log)


def _orch(**kwargs):
    return OpsPatchOrchestrator(_provider(**kwargs), logger=log)


def _cfg():
    return get_section(globals().get("__salt__", {}), "ops_patch", {})


def _pak_cfg():
    return _cfg().get("pak", {}) or {}


def _life_cfg():
    return _cfg().get("lifecycle", {}) or {}


def _pak_source(default=None):
    pak = _pak_cfg()
    return pak.get("source") or _cfg().get("pak_source") or default


def _destination(default=None):
    pak = _pak_cfg()
    return pak.get("destination") or default


def _last_install_file():
    cachedir = (globals().get("__opts__", {}) or {}).get("cachedir") or "/var/cache/salt"
    return os.path.join(cachedir, "vcf_ops_patch_last_install.json")


def _save_last_install(result):
    data = (result or {}).get("data") or {}
    if not data.get("pak_id") and not data.get("pak_status_path"):
        return
    try:
        with open(_last_install_file(), "w", encoding="utf-8") as fh:
            json.dump(
                {"pak_id": data.get("pak_id"), "pak_status_path": data.get("pak_status_path")}, fh
            )
    except OSError as exc:
        log.warning("Unable to record last VCF Operations pak install: %s", exc)


def _load_last_install():
    try:
        with open(_last_install_file(), encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (OSError, ValueError):
        return {}


def get_cluster_status(**kwargs):
    return _provider(**kwargs).get_cluster_status()


def get_cluster_nodes(**kwargs):
    return _provider(**kwargs).get_cluster_nodes()


def get_upgrade_status(**kwargs):
    return _provider(**kwargs).get_upgrade_status()


def get_system_status(**kwargs):
    return _provider(**kwargs).get_system_status()


def validate_cluster_health(dry_run=False, **kwargs):
    return _orch(**kwargs).cluster_health_validated(dry_run=as_bool(dry_run, False))


def download_pak(
    pak_source=None,
    destination=None,
    download_dir=None,
    download_timeout=None,
    verify_download_ssl=None,
    checksum=None,
    calculate_checksum=None,
    dry_run=False,
    **kwargs,
):
    pak = _pak_cfg()
    life = _life_cfg()
    return _orch(**kwargs).pak_downloaded(
        pak_source=pak_source or _pak_source(),
        destination=destination or _destination(),
        download_dir=download_dir or life.get("download_dir", _cfg().get("download_dir", "/tmp")),
        download_timeout=as_int(
            (
                life.get("download_timeout_seconds", _cfg().get("download_timeout", 1800))
                if download_timeout is None
                else download_timeout
            ),
            1800,
        ),
        verify_download_ssl=as_bool(
            (
                pak.get("verify_download_ssl", _cfg().get("verify_download_ssl", False))
                if verify_download_ssl is None
                else verify_download_ssl
            ),
            False,
        ),
        checksum=checksum if checksum is not None else pak.get("checksum"),
        calculate_checksum=as_bool(
            (
                pak.get("calculate_checksum", False)
                if calculate_checksum is None
                else calculate_checksum
            ),
            False,
        ),
        dry_run=as_bool(dry_run, False),
    )


def install_pak(
    pak_file=None, pak_handling_advice=None, install_timeout=None, dry_run=False, **kwargs
):
    pak = _pak_cfg()
    life = _life_cfg()
    result = _orch(**kwargs).pak_installed(
        pak_file=pak_file or pak.get("destination") or _pak_source(),
        pak_handling_advice=pak_handling_advice
        or pak.get("handling_advice", _cfg().get("pak_handling_advice", "CLOBBER")),
        install_timeout=as_int(
            (
                life.get("install_timeout_seconds", _cfg().get("install_timeout", 7200))
                if install_timeout is None
                else install_timeout
            ),
            7200,
        ),
        dry_run=as_bool(dry_run, False),
    )
    if not as_bool(dry_run, False):
        _save_last_install(result)
    return result


def wait_for_upgrade(
    timeout_seconds=None,
    poll_interval_seconds=None,
    pak_id=None,
    pak_status_path=None,
    max_transient_errors=None,
    **kwargs,
):
    life = _life_cfg()
    pak = _pak_cfg()
    pak_id = pak_id or pak.get("id") or pak.get("pak_id")
    pak_status_path = pak_status_path or pak.get("status_path") or pak.get("pak_status_path")
    if not pak_id and not pak_status_path:
        last = _load_last_install()
        pak_id, pak_status_path = last.get("pak_id"), last.get("pak_status_path")
    return _orch(**kwargs).upgrade_monitored(
        timeout_seconds=as_int(
            (
                life.get("upgrade_timeout_seconds", 14400)
                if timeout_seconds is None
                else timeout_seconds
            ),
            14400,
        ),
        poll_interval_seconds=as_int(
            (
                life.get("poll_interval_seconds", 60)
                if poll_interval_seconds is None
                else poll_interval_seconds
            ),
            60,
        ),
        pak_id=pak_id,
        pak_status_path=pak_status_path,
        max_transient_errors=as_int(
            (
                life.get("max_transient_errors", 0)
                if max_transient_errors is None
                else max_transient_errors
            ),
            0,
        ),
    )


def wait_for_cluster_online(timeout_seconds=None, poll_interval_seconds=None, **kwargs):
    life = _life_cfg()
    return _orch(**kwargs).cluster_online_verified(
        timeout_seconds=as_int(
            (
                life.get("cluster_online_timeout_seconds", 7200)
                if timeout_seconds is None
                else timeout_seconds
            ),
            7200,
        ),
        poll_interval_seconds=as_int(
            (
                life.get("poll_interval_seconds", 60)
                if poll_interval_seconds is None
                else poll_interval_seconds
            ),
            60,
        ),
    )


def full_upgrade(dry_run=False, **kwargs):
    pak = _pak_cfg()
    life = _life_cfg()
    return _orch(**kwargs).full_upgrade(
        pak_source=_pak_source(),
        destination=_destination(),
        pak_handling_advice=pak.get(
            "handling_advice", _cfg().get("pak_handling_advice", "CLOBBER")
        ),
        download_dir=life.get("download_dir", _cfg().get("download_dir", "/tmp")),
        download_timeout=as_int(
            life.get("download_timeout_seconds", _cfg().get("download_timeout", 1800)), 1800
        ),
        install_timeout=as_int(
            life.get("install_timeout_seconds", _cfg().get("install_timeout", 7200)), 7200
        ),
        monitor=as_bool(life.get("monitor", _cfg().get("monitor", True)), True),
        upgrade_timeout_seconds=as_int(
            life.get("upgrade_timeout_seconds", _cfg().get("upgrade_timeout_seconds", 14400)), 14400
        ),
        cluster_online_timeout_seconds=as_int(
            life.get(
                "cluster_online_timeout_seconds", _cfg().get("cluster_online_timeout_seconds", 7200)
            ),
            7200,
        ),
        poll_interval_seconds=as_int(
            life.get("poll_interval_seconds", _cfg().get("poll_interval_seconds", 60)), 60
        ),
        verify_download_ssl=as_bool(
            pak.get("verify_download_ssl", _cfg().get("verify_download_ssl", False)), False
        ),
        validate_health=as_bool(
            life.get("validate_health", _cfg().get("validate_health", True)), True
        ),
        checksum=pak.get("checksum"),
        calculate_checksum=as_bool(pak.get("calculate_checksum", False), False),
        dry_run=as_bool(dry_run, False),
    )


def report(**kwargs):
    return _orch(**kwargs).reported()


# Backward-compatible execution alias from v1.1.0
def pak_installed(**kwargs):
    return install_pak(**kwargs)
