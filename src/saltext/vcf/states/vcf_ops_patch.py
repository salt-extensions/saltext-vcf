# pylint: disable=broad-exception-caught
import logging

log = logging.getLogger(__name__)
__virtualname__ = "vcf_ops_patch"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "result": True, "changes": {}, "comment": ""}


def _apply(ret, result):
    ret["result"] = bool(result.get("success", result.get("result", True)))
    ret["comment"] = result.get("comment", "")
    ret["changes"] = result.get("changes", {}) if result.get("changed") else {}
    if result.get("changed") and __opts__.get("test", False):
        ret["result"] = None
    return ret


def _fail(ret, exc):
    log.exception("ops_patch state failed")
    ret["result"] = False
    ret["comment"] = str(exc)
    return ret


def cluster_health_validated(name, **kwargs):
    ret = _ret(name)
    try:
        return _apply(
            ret,
            __salt__["vcf_ops_patch.validate_cluster_health"](
                dry_run=__opts__.get("test", False), **kwargs
            ),
        )
    except Exception as exc:
        return _fail(ret, exc)


def pak_downloaded(name, **kwargs):
    ret = _ret(name)
    try:
        return _apply(
            ret,
            __salt__["vcf_ops_patch.download_pak"](dry_run=__opts__.get("test", False), **kwargs),
        )
    except Exception as exc:
        return _fail(ret, exc)


def pak_installed(name, **kwargs):
    ret = _ret(name)
    try:
        return _apply(
            ret,
            __salt__["vcf_ops_patch.install_pak"](dry_run=__opts__.get("test", False), **kwargs),
        )
    except Exception as exc:
        return _fail(ret, exc)


def _would_wait(ret, comment):
    ret["result"] = None
    ret["comment"] = comment
    return ret


def upgrade_monitored(name, **kwargs):
    ret = _ret(name)
    if __opts__.get("test", False):
        return _would_wait(ret, "VCF Operations upgrade would be monitored until completion")
    try:
        return _apply(ret, __salt__["vcf_ops_patch.wait_for_upgrade"](**kwargs))
    except Exception as exc:
        return _fail(ret, exc)


def cluster_online_verified(name, **kwargs):
    ret = _ret(name)
    if __opts__.get("test", False):
        return _would_wait(ret, "VCF Operations cluster would be verified online")
    try:
        return _apply(ret, __salt__["vcf_ops_patch.wait_for_cluster_online"](**kwargs))
    except Exception as exc:
        return _fail(ret, exc)


def full_upgrade(name, **kwargs):
    ret = _ret(name)
    try:
        return _apply(
            ret,
            __salt__["vcf_ops_patch.full_upgrade"](dry_run=__opts__.get("test", False), **kwargs),
        )
    except Exception as exc:
        return _fail(ret, exc)


def reported(name, **kwargs):
    ret = _ret(name)
    try:
        return _apply(ret, __salt__["vcf_ops_patch.report"](**kwargs))
    except Exception as exc:
        return _fail(ret, exc)
