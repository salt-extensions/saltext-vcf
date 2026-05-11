"""``test`` module override for the ``vcenter`` resource type.

Loaded by the per-type resource loader for jobs dispatched to vCenter
resources. Delegates ``test.ping`` to :func:`saltext.vmware.resources.vcenter.ping`
so the result reflects actual reachability of the targeted vCenter.
"""

import logging

log = logging.getLogger(__name__)


def ping():
    """Return ``True`` if the targeted vCenter is reachable."""
    return __resource_funcs__["vcenter.ping"]()  # pylint: disable=undefined-variable
