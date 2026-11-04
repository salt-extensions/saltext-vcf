# pylint: disable=broad-exception-caught
import logging
import time

from saltext.vcf.clients.ops_client import OpsClient
from saltext.vcf.utils.file_utils import resolve_local_file

try:
    from salt.exceptions import CommandExecutionError
except Exception:

    class CommandExecutionError(Exception):
        pass


GOOD_CLUSTER_STATES = {"INITIALIZED", "ONLINE", "RUNNING", "READY", "CONFIGURED"}
GOOD_NODE_STATES = {"CONFIGURED", "ONLINE", "RUNNING", "READY"}
BAD_CLUSTER_STATES = {"FAILED", "ERROR", "OFFLINE", "UNREACHABLE", "UNKNOWN", "DEGRADED"}
BAD_NODE_STATES = {"FAILED", "ERROR", "OFFLINE", "UNREACHABLE", "UNKNOWN"}


class OpsPatchProvider:
    def __init__(
        self,
        host,
        username,
        password,
        protocol="https",
        port=443,
        verify_ssl=False,
        timeout=300,
        logger=None,
    ):
        self.log = logger or logging.getLogger(__name__)
        self.client = OpsClient(
            host=host,
            username=username,
            password=password,
            protocol=protocol,
            port=port,
            verify_ssl=verify_ssl,
            timeout=timeout,
            logger=self.log,
        )

    def get_cluster_status(self):
        return self.client.get_cluster_status()

    def get_cluster_nodes(self):
        return self.client.get_cluster_nodes()

    def get_upgrade_status(self, pak_id=None, pak_status_path=None):
        return self.client.get_upgrade_status(pak_id=pak_id, pak_status_path=pak_status_path)

    def get_system_status(self):
        return self.client.get_system_status()

    def resolve_pak_file(
        self,
        pak_source,
        destination=None,
        download_dir="/tmp",
        download_timeout=1800,
        verify_ssl=False,
        checksum=None,
        calculate_checksum=False,
    ):
        return resolve_local_file(
            pak_source,
            destination=destination,
            download_dir=download_dir,
            requests_session=self.client.session,
            verify_ssl=verify_ssl,
            timeout=download_timeout,
            logger=self.log,
            checksum=checksum,
            calculate_checksum=calculate_checksum,
        )

    def upload_and_install_pak(self, pak_file, pak_handling_advice="CLOBBER", timeout=7200):
        return self.client.upload_and_install_pak(
            pak_file=pak_file, pak_handling_advice=pak_handling_advice, timeout=timeout
        )

    def wait_for_cluster_online(self, timeout_seconds=7200, poll_interval_seconds=60):
        start = time.time()
        last = None
        while True:
            try:
                status = self.get_cluster_status()
                last = status
                health = self.cluster_health(status)
                self.log.info(
                    "VCF Operations cluster health=%s state=%s nodes=%s",
                    health.get("healthy"),
                    health.get("cluster_state"),
                    health.get("node_states"),
                )
                if health.get("healthy"):
                    return {"success": True, "status": status, "health": health}
            except Exception as exc:
                last = str(exc)
                self.log.warning("Unable to read VCF Operations cluster status: %s", exc)
            if time.time() - start > timeout_seconds:
                raise CommandExecutionError(
                    f"Timed out waiting for VCF Operations cluster to become healthy. Last status: {last}"
                )
            time.sleep(poll_interval_seconds)

    def get_pak_status(self, pak_id=None, pak_status_path=None):
        return self.client.get_pak_status(pak_id=pak_id, pak_status_path=pak_status_path)

    def wait_for_upgrade_completion(
        self,
        timeout_seconds=14400,
        poll_interval_seconds=60,
        pak_id=None,
        pak_status_path=None,
        max_transient_errors=None,
    ):
        """
        Poll the installed pak's CASA status until the install completes.

        Succeeds when ``cluster_pak_install_status`` is ``COMPLETED`` and fails
        when the cluster or any slice reports ``FAILED``. Request errors (for
        example while Operations restarts mid-upgrade) are transient: they are
        retried until the timeout, or until ``max_transient_errors`` consecutive
        errors when that is set.
        """
        if not pak_id and not pak_status_path:
            raise CommandExecutionError(
                "Cannot monitor the VCF Operations upgrade without a pak id or status path. "
                "Pass pak_id, or run install_pak first so the id is recorded."
            )
        start = time.time()
        last = None
        last_progress = None
        transient_errors = 0
        while True:
            try:
                status = self.get_pak_status(pak_id=pak_id, pak_status_path=pak_status_path)
            except Exception as exc:
                last = str(exc)
                transient_errors += 1
                self.log.warning(
                    "VCF Operations upgrade status unavailable (%s). Services may be restarting: %s",
                    transient_errors,
                    exc,
                )
                if max_transient_errors and transient_errors >= max_transient_errors:
                    raise CommandExecutionError(
                        f"VCF Operations upgrade status unavailable after {max_transient_errors} attempts. Last error: {exc}"
                    ) from exc
            else:
                transient_errors = 0
                last = status
                progress = self._pak_install_state(status)
                key = (
                    progress["cluster_status"],
                    tuple((s["state"], s["status"]) for s in progress["slices"]),
                )
                log = self.log.info if key != last_progress else self.log.debug
                log(
                    "VCF Operations upgrade cluster_status=%s slices=%s",
                    progress["cluster_status"],
                    [(s["address"], s["state"], s["status"]) for s in progress["slices"]],
                )
                last_progress = key
                if progress["cluster_status"] == "FAILED" or any(
                    s["status"] == "FAILED" for s in progress["slices"]
                ):
                    raise CommandExecutionError(f"VCF Operations upgrade failed: {status}")
                if progress["cluster_status"] == "COMPLETED":
                    return {"success": True, "status": status, "progress": progress}
            if time.time() - start > timeout_seconds:
                raise CommandExecutionError(
                    f"Timed out waiting for VCF Operations upgrade completion. Last status: {last}"
                )
            time.sleep(poll_interval_seconds)

    @staticmethod
    def _pak_install_state(status):
        """Extract the cluster and per-slice install status from a CASA pak status response."""
        response = (status or {}).get("response") or {}
        slices = []
        for item in response.get("slices") or []:
            document = (item or {}).get("document") or {}
            slices.append(
                {
                    "address": (item or {}).get("slice_address"),
                    "state": str(document.get("pak_state") or "").upper(),
                    "status": str(document.get("pak_install_status") or "").upper(),
                }
            )
        return {
            "cluster_status": str(response.get("cluster_pak_install_status") or "").upper(),
            "slices": slices,
        }

    @staticmethod
    def cluster_health(status):
        if not isinstance(status, dict):
            return {
                "healthy": False,
                "reason": "Cluster status is not a dictionary",
                "status": status,
            }
        cluster_state = str(status.get("cluster_state") or status.get("state") or "").upper()
        nodes = status.get("nodes_states") or status.get("nodes") or []
        if cluster_state in BAD_CLUSTER_STATES:
            return {
                "healthy": False,
                "reason": f"Cluster state is bad: {cluster_state}",
                "cluster_state": cluster_state,
                "nodes": nodes,
            }
        node_states = []
        bad_nodes = []
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    state = str(node.get("state") or node.get("status") or "").upper()
                    node_states.append(state)
                    if state in BAD_NODE_STATES:
                        bad_nodes.append(node)
        if bad_nodes:
            return {
                "healthy": False,
                "reason": "One or more nodes are unhealthy",
                "cluster_state": cluster_state,
                "node_states": node_states,
                "bad_nodes": bad_nodes,
            }
        if (cluster_state in GOOD_CLUSTER_STATES or not cluster_state) and all(
            (not s) or s in GOOD_NODE_STATES for s in node_states
        ):
            return {
                "healthy": True,
                "reason": "Cluster is healthy for upgrade",
                "cluster_state": cluster_state,
                "node_states": node_states,
            }
        return {
            "healthy": False,
            "reason": "Cluster/node state is not in accepted healthy states",
            "cluster_state": cluster_state,
            "node_states": node_states,
        }
