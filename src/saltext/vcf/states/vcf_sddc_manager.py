"""State module for SDDC Manager readiness."""

from saltext.vcf.clients import sddc_manager as r

__virtualname__ = "vcf_sddc_manager"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def ready(name, profile=None):
    """Ensure SDDC Manager responds to its singleton info endpoint."""
    ret = _ret(name)
    info = r.get_or_none(__opts__, profile=profile)  # noqa: F821
    if info is None:
        ret["result"] = False
        ret["comment"] = f"SDDC Manager {name} is not reachable"
        return ret
    ret["comment"] = f"SDDC Manager {name} is reachable"
    ret["changes"] = {}
    return ret


def deployed(name, topology=None, connection=None, profile=None):
    """Reference-compatible alias for :func:`ready`.

    Management-domain deployment is owned by the VCF Installer bringup state;
    this state verifies the resulting SDDC Manager endpoint.
    """
    return ready(name, profile=profile)
