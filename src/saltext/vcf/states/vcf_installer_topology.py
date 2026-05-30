"""State module for VCF Installer workflow pillar validation."""

from saltext.vcf.modules import vcf_installer_topology as m

__virtualname__ = "vcf_installer_topology"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def valid(name, spec=None):
    """Ensure the VCF Installer workflow pillar is structurally valid."""
    ret = _ret(name)
    result = m.validate(spec)
    if result.get("valid"):
        warnings = result.get("warnings") or []
        ret["comment"] = "topology valid" if not warnings else "; ".join(warnings)
        return ret
    ret["result"] = False
    ret["comment"] = "; ".join(result.get("errors") or ["topology validation failed"])
    return ret
