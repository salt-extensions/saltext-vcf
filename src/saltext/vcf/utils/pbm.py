"""Storage Policy-Based Management (SPBM) SOAP connection helper.

vCenter's modern REST API (``/api/vcenter/storage/policies``) only lists and
reads storage policies — authoring (create/update/delete) has never been
exposed there. The only path is the separate PBM SOAP service at
``/pbm/sdk``, which ``pyVmomi`` exposes as the ``pbm`` package. Like
:mod:`saltext.vcf.utils.vsan`, the PBM stub reuses the vCenter SOAP session
cookie from :mod:`saltext.vcf.utils.vim` rather than authenticating
separately.
"""

import ssl

from pyVmomi import SoapStubAdapter
from pyVmomi import VmomiSupport
from pyVmomi import pbm

from saltext.vcf.utils import vim as vim_utils

# Cached PBM stub per (host, username).
_PBM_STUB_CACHE: dict[str, SoapStubAdapter] = {}


def get_stub(opts, profile=None):
    """Return a PBM SOAP stub bound to the same session as ``utils.vim``."""
    cfg = vim_utils.get_config(opts, profile=profile)
    key = f"{cfg['host']}:{cfg['username']}"
    cached = _PBM_STUB_CACHE.get(key)
    if cached is not None:
        return cached

    si = vim_utils.get_service_instance(opts, profile=profile)
    sslContext = (  # noqa: N806  pylint: disable=invalid-name
        None if cfg["verify_ssl"] else ssl._create_unverified_context()
    )
    stub = SoapStubAdapter(
        host=cfg["host"],
        version=VmomiSupport.newestVersions.Get("pbm"),
        path="/pbm/sdk",
        poolSize=0,
        sslContext=sslContext,
    )
    stub.cookie = si._stub.cookie  # noqa: SLF001
    _PBM_STUB_CACHE[key] = stub
    return stub


def invalidate_stub(opts, profile=None):
    cfg = vim_utils.get_config(opts, profile=profile)
    _PBM_STUB_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


def profile_manager(opts, profile=None):
    """``pbm.profile.ProfileManager`` — the entry point for PBM policy CRUD."""
    si = pbm.ServiceInstance("ServiceInstance", get_stub(opts, profile=profile))
    return si.RetrieveContent().profileManager
