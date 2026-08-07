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
from http.cookies import SimpleCookie

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
    stub_kwargs = {
        "host": cfg["host"],
        "version": VmomiSupport.newestVersions.Get("pbm"),
        "path": "/pbm/sdk",
        "poolSize": 0,
        "sslContext": sslContext,
    }
    # Same VCF 9.x local-envoy-proxy requirement as the main /sdk connection
    # (see utils.vim._proxy_for_host) -- this stub is built independently of
    # get_service_instance()'s SmartConnect call, so it needs the same
    # explicit httpProxyHost/httpProxyPort or it gets ConnectionRefusedError
    # even though the main vim connection succeeds.
    proxy_host, proxy_port = vim_utils._proxy_for_host(cfg["host"])  # noqa: SLF001
    if proxy_host:
        stub_kwargs["httpProxyHost"] = proxy_host
        stub_kwargs["httpProxyPort"] = proxy_port
    stub = SoapStubAdapter(**stub_kwargs)
    stub.cookie = si._stub.cookie  # noqa: SLF001

    # Unlike vim25/vsanHealth (which accept the plain HTTP Cookie header
    # above), PBM validates sessions through a separate VMODL
    # request-context field -- without this, every PBM call fails with
    # vim.fault.NotAuthenticated even though the stub connects and the
    # Cookie header is set correctly. This is the standard pattern VMware's
    # own PBM sample scripts use to reuse an existing vim25 session.
    vc_session_id = si._stub.cookie.split('"')[1]  # noqa: SLF001
    http_context = VmomiSupport.GetHttpContext()
    cookie_jar = SimpleCookie()
    cookie_jar["vmware_soap_session"] = vc_session_id
    http_context["cookies"] = cookie_jar
    VmomiSupport.GetRequestContext()["vcSessionCookie"] = vc_session_id

    _PBM_STUB_CACHE[key] = stub
    return stub


def invalidate_stub(opts, profile=None):
    cfg = vim_utils.get_config(opts, profile=profile)
    _PBM_STUB_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


def profile_manager(opts, profile=None):
    """``pbm.profile.ProfileManager`` — the entry point for PBM policy CRUD."""
    si = pbm.ServiceInstance("ServiceInstance", get_stub(opts, profile=profile))
    return si.RetrieveContent().profileManager
