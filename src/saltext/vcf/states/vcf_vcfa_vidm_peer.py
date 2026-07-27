"""State module for the vRA→vIDM peer TLS trust anchor.

Enforces a specific PEM in the vIDM peer config. Compares the current
``peerCertificate`` field byte-for-byte (after ``.strip()``) and only
issues a PUT when it differs.
"""

from saltext.vcf.clients import vcfa_vidm_peer as c

__virtualname__ = "vcf_vcfa_vidm_peer"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _norm(pem):
    return (pem or "").strip()


def cert_present(name, cert, profile=None):
    """Ensure vIDM peer trust cert equals *cert* (PEM string).

    *name* is used for the state ID / comment; the actual resource is
    singleton on the appliance.
    """
    ret = _ret(name)
    current = c.vidm_peer_get(__opts__, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = (
            "vIDM peer resource not found (this appliance may not have a vIDM peer configured)"
        )
        return ret

    if _norm(current.get("peerCertificate")) == _norm(cert):
        ret["comment"] = f"vIDM peer cert for {name} already matches"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vIDM peer cert for {name} would be replaced"
        ret["changes"] = {"peerCertificate": {"old": "<redacted>", "new": "<redacted>"}}
        return ret

    c.vidm_peer_set(__opts__, cert=cert, profile=profile)
    ret["changes"] = {"peerCertificate": {"old": "<redacted>", "new": "<redacted>"}}
    ret["comment"] = f"vIDM peer cert for {name} replaced"
    return ret
