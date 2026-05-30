"""
Salt Resources framework integration for VMware.

Each subpackage (:mod:`saltext.vcf.resources.vcenter`,
:mod:`saltext.vcf.resources.sddc`, :mod:`saltext.vcf.resources.nsx`)
implements the per-type resource interface described in
``salt.resources``: ``__virtual__``, :func:`init`, :func:`initialized`,
:func:`discover`, :func:`grains`, :func:`grains_refresh`, :func:`ping`,
:func:`shutdown`, plus per-resource operations.

A minion that manages several vCenters declares them in pillar under the
configured resource key (``resources`` by default)::

    resources:
      vcenter:
        instances:
          mgmt-vc:
            host: mgmt-vc.example.test
            username: administrator@vsphere.local
            password: secret
            verify_ssl: false
          prod-vc:
            host: prod-vc.example.com
            username: administrator@vsphere.local
            password: secret
      sddc:
        instances:
          sddc-01: { host: sddc-manager.example.test, ... }
      nsx:
        instances:
          mgmt-nsx: { host: mgmt-nsx.example.test, ... }

After :func:`discover` runs (via ``saltutil.refresh_resources``) the master's
Resource Registry knows which IDs each minion manages, so users can target
specific instances::

    salt -C 'T@vcenter:mgmt-vc' vcf_cluster.list_

The current resource ID is conveyed to per-resource functions via the
``__resource__`` dunder injected by the loader, not as a parameter.

These per-type packages delegate all REST work to
:mod:`saltext.vcf.clients`, so the only resource-framework-specific
concerns here are config lookup, ``__context__`` caching, and the framework
interface.
"""

try:
    from salt.utils.resources import pillar_resources_tree
except ImportError:  # Salt versions without the Resources framework

    def pillar_resources_tree(opts):
        """Fallback: read ``opts['pillar']['resources']`` directly."""
        pillar = opts.get("pillar", {}) or {}
        sub = pillar.get(opts.get("resource_pillar_key", "resources"), {})
        return sub if isinstance(sub, dict) else {}


__all__ = ["pillar_resources_tree"]
