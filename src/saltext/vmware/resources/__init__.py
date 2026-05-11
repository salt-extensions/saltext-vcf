"""
Salt Resources framework integration for VMware.

Each subpackage (:mod:`saltext.vmware.resources.vcenter`,
:mod:`saltext.vmware.resources.sddc`, :mod:`saltext.vmware.resources.nsx`)
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
            host: mgmt-vc.vcf.nimbus.internal
            username: administrator@vsphere.local
            password: VMware123!
            verify_ssl: false
          prod-vc:
            host: prod-vc.example.com
            username: administrator@vsphere.local
            password: secret
      sddc:
        instances:
          sddc-01: { host: sddc-manager.vcf.nimbus.internal, ... }
      nsx:
        instances:
          mgmt-nsx: { host: mgmt-nsx.vcf.nimbus.internal, ... }

After :func:`discover` runs (via ``saltutil.refresh_resources``) the master's
Resource Registry knows which IDs each minion manages, so users can target
specific instances::

    salt -C 'T@vcenter:mgmt-vc' vmware_cluster.list_

The current resource ID is conveyed to per-resource functions via the
``__resource__`` dunder injected by the loader, not as a parameter.

These per-type packages delegate all REST work to
:mod:`saltext.vmware.clients`, so the only resource-framework-specific
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
