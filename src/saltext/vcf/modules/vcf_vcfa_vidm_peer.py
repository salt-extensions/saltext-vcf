"""Execution module for VCF Automation vRA→vIDM peer trust.

Wraps :mod:`saltext.vcf.clients.vcfa_vidm_peer`. Used to satisfy the
"vRA communication to vIDM must use a valid TLS certificate"
912-controls gap by allowing the peer certificate PEM to be inspected
and rotated from ``salt-call``.

CLI Example:

.. code-block:: bash

    salt '*' vcf_vcfa_vidm_peer.get
    salt '*' vcf_vcfa_vidm_peer.set cert="$(cat /etc/ssl/vidm-ca.pem)"
"""

from saltext.vcf.clients import vcfa_vidm_peer as c

__virtualname__ = "vcf_vcfa_vidm_peer"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Return the current vIDM peer config."""
    return c.vidm_peer_get(__opts__, profile=profile)


def set_(cert=None, host=None, client_id=None, client_secret=None, profile=None):
    """PUT vIDM peer config (merging over current)."""
    return c.vidm_peer_set(
        __opts__,
        cert=cert,
        host=host,
        client_id=client_id,
        client_secret=client_secret,
        profile=profile,
    )


def validate(spec, profile=None):
    """Dry-run a candidate vIDM peer config."""
    return c.vidm_peer_validate(__opts__, spec, profile=profile)
