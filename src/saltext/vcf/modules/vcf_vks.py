"""VKS bridge — Supervisor kubeconfig fetch, optional saltext-kubernetes handoff.

This module gives an operator a single call to materialize a Supervisor
kubeconfig (writing it to disk) so subsequent calls into the
``saltext-kubernetes`` extension can talk to the Supervisor API server.
The bridge is intentionally thin: it does NOT depend on
``saltext-kubernetes`` at import time. Install the ``vks`` extra
(``pip install 'saltext.vcf[vks]'``) to get the runtime dependency.
"""

import os
import stat

from saltext.vcf.clients import vcenter_supervisor_kubeconfig

__virtualname__ = "vcf_vks"


def __virtual__():
    return __virtualname__


def fetch_kubeconfig(cluster_id, path=None, namespace=None, profile=None):
    """Fetch a Supervisor kubeconfig and (optionally) write it to *path*.

        Returns a dict ``{"path": ..., "kubeconfig": "<yaml>"}``. When *path*
        is omitted, the file is written to ``~/.kube/vks-<cluster_id>.config``.
        The file is created with mode 0o600.

        If *namespace* is provided, fetches a namespace-scoped kubeconfig
        (limits the user to that single namespace).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vks.fetch_kubeconfig <cluster_id> <path> <namespace>

    """
    if namespace:
        kubeconfig = vcenter_supervisor_kubeconfig.get_kubeconfig_for_namespace(
            __opts__, namespace, profile=profile
        )
    else:
        kubeconfig = vcenter_supervisor_kubeconfig.get_kubeconfig(
            __opts__, cluster_id, profile=profile
        )
    if path is None:
        kubedir = os.path.expanduser("~/.kube")
        os.makedirs(kubedir, exist_ok=True)
        path = os.path.join(kubedir, f"vks-{cluster_id}.config")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(kubeconfig if isinstance(kubeconfig, str) else str(kubeconfig))
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return {"path": path, "kubeconfig": kubeconfig}


def saltext_kubernetes_available():
    """Probe whether the ``saltext-kubernetes`` extension is importable.

        Returns ``True`` when ``saltext.kubernetes`` and its ``kubernetes``
        client dependency are present in the current Python environment.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vks.saltext_kubernetes_available

    """
    try:
        import kubernetes  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
        import saltext.kubernetes  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
    except ImportError:
        return False
    return True
