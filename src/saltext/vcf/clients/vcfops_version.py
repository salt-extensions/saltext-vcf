"""VCF Operations — versions (/suite-api/api/versions)."""

from saltext.vcf.utils import vcfops


def get(opts):
    """Return suite-api version info."""
    return vcfops.api_get(opts, "/suite-api/api/versions")
