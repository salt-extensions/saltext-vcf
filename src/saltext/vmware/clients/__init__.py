"""
Internal API-client layer.

Each module here owns the REST endpoint paths, request body shapes, and
404-tolerant ``get_or_none`` lookups for one VMware object type (cluster,
host, segment, etc.). They are plain Python helpers — no Salt context or
``__resource__`` dunder — and take ``(opts, ...)`` so they can be called
from anywhere: standalone execution modules, state modules, or the Salt
Resources framework at :mod:`saltext.vmware.resources`.
"""
