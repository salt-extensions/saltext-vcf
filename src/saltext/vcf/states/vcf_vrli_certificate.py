"""State module for the vRLI appliance certificate.

Idempotency: the state parses the leaf ``cert`` PEM to extract its
serial number (a hex string) and compares it to the ``serialNum``
reported by ``GET /api/v2/certificate``. Reinstalls only when they
differ. Requires the standard-library ``ssl`` module (bundled).
"""

import binascii
import re

from saltext.vcf.clients import vrli_certificate as c

__virtualname__ = "vcf_vrli_certificate"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


_HEX_ONLY = re.compile(r"[^0-9a-fA-F]")


def _serial_from_pem(pem):
    """Return the leaf serial as a lowercase hex string (no ``0x``, no ``:``).

    We use ``ssl.PEM_cert_to_DER_cert`` + a minimal ASN.1 walk so we
    don't pull in ``cryptography`` for a build that already ships
    only ``requests`` + ``paramiko``.
    """
    import ssl as _ssl

    try:
        der = _ssl.PEM_cert_to_DER_cert(pem)
    except Exception as exc:  # noqa: BLE001 - normalize bad-PEM errors
        raise ValueError(f"could not parse PEM certificate: {exc}") from exc

    # Minimal ASN.1 walk to reach the tbsCertificate.serialNumber INTEGER.
    # Certificate ::= SEQUENCE {
    #     tbsCertificate       TBSCertificate,        <-- also a SEQUENCE
    #     signatureAlgorithm   ...,
    #     signatureValue       ... }
    # TBSCertificate ::= SEQUENCE {
    #     version         [0] EXPLICIT Version DEFAULT v1,   <-- optional
    #     serialNumber        CertificateSerialNumber,       <-- INTEGER
    #     ... }
    def _read_len(buf, idx):
        n = buf[idx]
        idx += 1
        if n & 0x80:
            n_bytes = n & 0x7F
            n = int.from_bytes(buf[idx : idx + n_bytes], "big")
            idx += n_bytes
        return n, idx

    def _consume(buf, idx):
        tag = buf[idx]
        idx += 1
        length, idx = _read_len(buf, idx)
        return tag, buf[idx : idx + length], idx + length

    _tag, cert_body, _end = _consume(der, 0)
    _tag, tbs_body, _end = _consume(cert_body, 0)
    idx = 0
    tag = tbs_body[idx]
    if tag == 0xA0:  # [0] EXPLICIT version
        _tag, _v, idx = _consume(tbs_body, idx)
    _tag, serial_bytes, _idx = _consume(tbs_body, idx)
    # Strip a leading 0x00 sign byte if the high bit of the next octet is set.
    if len(serial_bytes) > 1 and serial_bytes[0] == 0x00:
        serial_bytes = serial_bytes[1:]
    return binascii.hexlify(serial_bytes).decode()


def _normalize_serial(raw):
    if raw is None:
        return None
    return _HEX_ONLY.sub("", str(raw)).lower().lstrip("0") or "0"


def certificate_present(name, cert, key, chain=None, profile=None):
    """Ensure the appliance is presenting the given leaf certificate.

    *cert* — PEM string for the leaf.
    *key*  — PEM string for its private key.
    *chain* — optional intermediate chain PEM.

    Idempotency: compares the leaf's serial number against the
    ``serialNum`` field on ``GET /api/v2/certificate``. Non-matching
    triggers a POST that replaces the cert (which restarts the API
    listener — expect the next state in the run to reconnect).
    """
    ret = _ret(name)
    desired_serial = _normalize_serial(_serial_from_pem(cert))
    current = c.get(__opts__, profile=profile)
    current_serial = _normalize_serial(current.get("serialNum")) if current else None
    if current_serial == desired_serial:
        ret["comment"] = f"Appliance certificate already at serial {desired_serial}; no change"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = (
            f"Appliance certificate would be replaced ({current_serial!r} "
            f"-> {desired_serial!r}); API listener will restart"
        )
        return ret
    c.install(__opts__, cert, key, chain_pem=chain, profile=profile)
    ret["changes"] = {"serialNum": {"old": current_serial, "new": desired_serial}}
    ret["comment"] = (
        f"Installed new appliance certificate (serial {desired_serial}); " f"API listener restarted"
    )
    return ret
