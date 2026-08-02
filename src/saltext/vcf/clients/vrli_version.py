"""VCF Operations for Logs (vRLI) — product version.

``GET /api/v2/version`` returns ``{"releaseName": "...", "version": "..."}``.
"""

from saltext.vcf.utils import vrli

_VERSION = "/api/v2/version"


def get(opts, profile=None):
    """Return the product version + release name."""
    return vrli.api_get(opts, _VERSION, profile=profile)
