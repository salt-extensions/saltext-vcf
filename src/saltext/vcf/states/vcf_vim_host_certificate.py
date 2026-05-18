"""State module for ESXi host SSL certificate."""

from saltext.vcf.clients import vim_host_certificate as c

__virtualname__ = "vcf_vim_host_certificate"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, host=None, cert_pem=None, profile=None):
    """Ensure *host*'s installed cert PEM matches *cert_pem*.

    *name* informational; *host* defaults to *name*. Cert match is byte-for-byte.
    """
    host = host or name
    ret = _ret(name)
    if cert_pem is None:
        ret["result"] = False
        ret["comment"] = "cert_pem is required"
        return ret
    current = c.info(__opts__, host, profile=profile)
    cur_pem = (current.get("pem") or "").strip()
    if cur_pem == cert_pem.strip():
        ret["comment"] = f"cert on {host} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"cert on {host} would be replaced"
        return ret
    c.install_cert(__opts__, host, cert_pem, profile=profile)
    ret["changes"] = {"cert": "replaced"}
    ret["comment"] = f"cert on {host} installed"
    return ret
