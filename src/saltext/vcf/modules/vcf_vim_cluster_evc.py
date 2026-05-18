"""Execution module for cluster EVC mode."""

from saltext.vcf.clients import vim_cluster_evc as c

__virtualname__ = "vcf_vim_cluster_evc"


def __virtual__():
    return __virtualname__


def get(cluster, profile=None):
    """Return EVC state for *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_evc.get <cluster>
    """
    return c.get(__opts__, cluster, profile=profile)


def configure(cluster, evc_mode_key, profile=None):
    """Enable or change EVC mode on *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_evc.configure <cluster> intel-sandybridge
    """
    return c.configure(__opts__, cluster, evc_mode_key, profile=profile)


def disable(cluster, profile=None):
    """Disable EVC mode on *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_evc.disable <cluster>
    """
    return c.disable(__opts__, cluster, profile=profile)


def check(cluster, evc_mode_key, profile=None):
    """Dry-run check of an EVC mode change.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_evc.check <cluster> intel-sandybridge
    """
    return c.check(__opts__, cluster, evc_mode_key, profile=profile)
