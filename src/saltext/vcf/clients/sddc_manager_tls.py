"""TLS version and cipher profile probes for SDDC Manager.

Probes the remote SDDC Manager HTTPS listener using ``openssl s_client``
executed as a subprocess on the cloud proxy.  No credentials are required —
the probes are unauthenticated TLS handshake attempts.

Config is read from Salt opts/pillar under ``saltext.vcf.sddc_manager``
(same block used by all other SDDC Manager clients):

.. code-block:: yaml

    saltext.vcf:
      sddc_manager:
        host: sddc-manager.example.test
        username: administrator@vsphere.local
        password: secret
        verify_ssl: false
"""

import logging
import subprocess
from typing import Dict
from typing import List
from typing import Optional

from saltext.vcf.utils import sddc

log = logging.getLogger(__name__)

CMD_TIMEOUT = 10

# openssl flags for each TLS version
_TLS_FLAGS = [
    ("1.0", "-tls1"),
    ("1.1", "-tls1_1"),
    ("1.2", "-tls1_2"),
    ("1.3", "-tls1_3"),
]

# Cipher probes to distinguish NIST_2024 (GCM-only) from COMPATIBLE (CBC allowed)
_CIPHER_GCM = "ECDHE-RSA-AES256-GCM-SHA384"
_CIPHER_CBC = "AES256-SHA"

# A successful TLS handshake contains "New, TLSv" in stdout;
# a rejected handshake contains "New, (NONE)".
_ACCEPTED_SIGNAL = "New, TLSv"

PROFILE_NIST_2024_TLS13_ONLY = "NIST_2024_TLS_13_ONLY"
PROFILE_NIST_2024 = "NIST_2024"
PROFILE_COMPATIBLE = "COMPATIBLE"
PROFILE_MANUAL = "MANUAL"


def _probe(host: str, tls_flag: str, cipher: Optional[str] = None) -> bool:
    """Run a single ``openssl s_client`` probe against *host*:443.

    Sends ``Q\\n`` to stdin so the process exits immediately after the
    handshake rather than waiting for interactive input.

    :param host: SDDC Manager hostname or IP.
    :param tls_flag: TLS version flag, e.g. ``-tls1_2``.
    :param cipher: Optional cipher string for ``-cipher``.
    :return: ``True`` if the handshake was accepted.
    """
    cmd = ["openssl", "s_client", "-connect", f"{host}:443", tls_flag]
    if cipher:
        cmd += ["-cipher", cipher]
    try:
        result = subprocess.run(
            cmd,
            input=b"Q\n",
            capture_output=True,
            timeout=CMD_TIMEOUT,
        )
        stdout = result.stdout.decode("utf-8", errors="ignore")
        accepted = _ACCEPTED_SIGNAL in stdout
        log.debug("TLS probe %s cipher=%s → %s", tls_flag, cipher or "default", accepted)
        return accepted
    except Exception as exc:  # pragma: no cover – subprocess errors
        log.error("openssl probe failed (host=%s flag=%s): %s", host, tls_flag, exc)
        return False


def get_tls_min_version(opts, profile=None) -> Dict:
    """Return the minimum TLS version accepted by the SDDC Manager listener.

    Probes TLS 1.0 → 1.3 in order; the first accepted version is the minimum.

    :param opts: Salt opts / pillar dict.
    :param profile: Optional named profile key under ``saltext.vcf.profiles``.
    :return: ``{"min_version": str|None, "supported_versions": list}``
    """
    host = sddc.get_config(opts, profile=profile)["host"]
    supported: List[str] = []

    for version_str, flag in _TLS_FLAGS:
        if _probe(host, flag):
            supported.append(version_str)

    min_version = supported[0] if supported else None
    log.info("SDDC Manager %s TLS min=%s supported=%s", host, min_version, supported)
    return {"min_version": min_version, "supported_versions": supported}


def get_tls_profile(opts, profile=None) -> Dict:
    """Detect the TLS cipher profile active on the SDDC Manager listener.

    Detection logic (mirrors the mops config-modules controller):

    * TLS 1.2 rejected, TLS 1.3 accepted  → ``NIST_2024_TLS_13_ONLY``
    * TLS 1.2+1.3 accepted, GCM accepted, CBC rejected → ``NIST_2024``
    * TLS 1.2+1.3 accepted, CBC also accepted           → ``COMPATIBLE``
    * Any other result                                   → ``MANUAL``

    :param opts: Salt opts / pillar dict.
    :param profile: Optional named profile key.
    :return: ``{"profile": str, "supported_profiles": list}``
    """
    host = sddc.get_config(opts, profile=profile)["host"]

    tls12 = _probe(host, "-tls1_2")
    tls13 = _probe(host, "-tls1_3")
    log.debug("SDDC Manager %s TLS probes: 1.2=%s 1.3=%s", host, tls12, tls13)

    if not tls12 and tls13:
        detected = PROFILE_NIST_2024_TLS13_ONLY
    elif tls12:
        gcm = _probe(host, "-tls1_2", cipher=_CIPHER_GCM)
        cbc = _probe(host, "-tls1_2", cipher=_CIPHER_CBC)
        log.debug("Cipher probes: GCM=%s CBC=%s", gcm, cbc)
        if gcm and not cbc:
            detected = PROFILE_NIST_2024
        elif cbc:
            detected = PROFILE_COMPATIBLE
        else:
            detected = PROFILE_MANUAL
    else:
        detected = PROFILE_MANUAL

    log.info("SDDC Manager %s detected TLS profile: %s", host, detected)
    return {"profile": detected, "supported_profiles": [detected]}
