"""ESXi host SSL certificate management via ``CertificateManager``.

Hosts have an SSL cert used for management plane (vCenter ↔ ESXi, KMS,
SAML). Cert lifecycle: read PEM + expiry, generate CSR, install a signed
cert, refresh (re-fetch from KMS / VECS), refresh CA bundle.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for h in container.view:
            if name_or_id in (h._moId, h.name):  # noqa: SLF001
                return h
    finally:
        container.Destroy()
    raise LookupError(f"host {name_or_id!r} not found")


def _cm(host):
    cm = host.configManager.certificateManager
    if cm is None:
        raise RuntimeError(f"host {host.name!r} has no certificateManager")
    return cm


def info(opts, host, profile=None):
    """Return cert metadata: ``{issuer, subject, not_before, not_after, pem,
    days_until_expiry}``.
    """
    h = _host(opts, host, profile=profile)
    cert_info = h.config.certificate or b""
    pem = bytes(cert_info).decode("utf-8", errors="replace") if cert_info else ""
    cert_details = getattr(h.runtime, "certificateInfo", None)
    out = {
        "pem": pem,
        "issuer": getattr(cert_details, "issuer", None) if cert_details else None,
        "subject": getattr(cert_details, "subject", None) if cert_details else None,
        "not_before": (
            cert_details.notBefore.isoformat()
            if cert_details and getattr(cert_details, "notBefore", None)
            else None
        ),
        "not_after": (
            cert_details.notAfter.isoformat()
            if cert_details and getattr(cert_details, "notAfter", None)
            else None
        ),
        "status": getattr(cert_details, "status", None) if cert_details else None,
    }
    return out


def generate_csr(opts, host, useip=True, profile=None):
    """Generate a CSR for *host*. Returns the PEM-encoded CSR string."""
    h = _host(opts, host, profile=profile)
    return _cm(h).GenerateCertificateSigningRequest(useIpAddressAsCommonName=bool(useip))


def install_cert(opts, host, cert_pem, profile=None):
    """Install a signed certificate PEM on *host*. Synchronous."""
    h = _host(opts, host, profile=profile)
    _cm(h).InstallServerCertificate(cert=cert_pem)
    return True


def refresh_cert(opts, host, profile=None):
    """Re-fetch the certificate from the VECS / KMS store on *host*."""
    h = _host(opts, host, profile=profile)
    _cm(h).RefreshCertificate()
    return True


def refresh_ca_bundle(opts, host, profile=None):
    """Refresh the trusted CA bundle on *host*."""
    h = _host(opts, host, profile=profile)
    _cm(h).RefreshCACertificates()
    return True
