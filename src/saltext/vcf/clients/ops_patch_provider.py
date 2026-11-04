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

    def wait_for_upgrade_completion(
        self,
        timeout_seconds=14400,
        poll_interval_seconds=60,
        pak_id=None,
        pak_status_path=None,
        max_transient_errors=None,
    ):
        start = time.time()
        last = None
        last_progress_key = None
        transient_errors = 0
        while True:
            status = self.get_upgrade_status(pak_id=pak_id, pak_status_path=pak_status_path)
            last = status
            progress = self._extract_progress(status)
            if self._upgrade_status_unavailable(status):
                transient_errors += 1
                self.log.warning(
                    "VCF Operations upgrade status temporarily unavailable (%s). Services may be restarting.",
                    transient_errors,
                )
                if max_transient_errors and transient_errors >= max_transient_errors:
                    raise CommandExecutionError(
                        f"VCF Operations upgrade status unavailable after {max_transient_errors} attempts. Last status: {status}"
                    )
            else:
                transient_errors = 0
                progress_key = (
                    progress.get("state"),
                    progress.get("percent"),
                    progress.get("step"),
                )
                if progress_key != last_progress_key:
                    self.log.info(
                        "VCF Operations upgrade status=%s progress=%s step=%s",
                        progress.get("state"),
                        progress.get("percent"),
                        progress.get("step"),
                    )
                    last_progress_key = progress_key
                else:
                    self.log.debug(
                        "VCF Operations upgrade status=%s progress=%s step=%s",
                        progress.get("state"),
                        progress.get("percent"),
                        progress.get("step"),
                    )
                if self._upgrade_complete(status):
                    return {"success": True, "status": status, "progress": progress}
                if self._upgrade_failed(status):
                    raise CommandExecutionError(f"VCF Operations upgrade failed: {status}")
            if time.time() - start > timeout_seconds:
                raise CommandExecutionError(
                    f"Timed out waiting for VCF Operations upgrade completion. Last status: {last}"
                )
            time.sleep(poll_interval_seconds)

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

    @staticmethod
    def _upgrade_status_unavailable(status):
        text = str(status).lower()
        return (
            "'path': none" in text
            and "response': none" in text
            and (
                "http 503" in text
                or "service unavailable" in text
                or "operations is not available" in text
                or "will be redirected" in text
            )
        )

    @staticmethod
    def _extract_progress(status):
        def unwrap(obj):
            if isinstance(obj, dict):
                if "response" in obj:
                    return unwrap(obj["response"])
                if "value" in obj:
                    return unwrap(obj["value"])
            return obj

        def find_first(obj, keys):
            if isinstance(obj, dict):
                for key in keys:
                    if key in obj and obj.get(key) not in (None, ""):
                        return obj.get(key)
                for value in obj.values():
                    found = find_first(value, keys)
                    if found not in (None, ""):
                        return found
            elif isinstance(obj, list):
                for item in obj:
                    found = find_first(item, keys)
                    if found not in (None, ""):
                        return found
            return None

        data = unwrap(status)
        state = find_first(data, ("state", "status", "upgradeStatus", "cluster_state", "phase"))
        percent = find_first(
            data,
            (
                "percentage",
                "percent",
                "progress",
                "progressPercentage",
                "percentComplete",
                "completedPercentage",
                "completionPercentage",
            ),
        )
        step = find_first(
            data,
            (
                "currentStep",
                "current_step",
                "step",
                "stage",
                "phase",
                "description",
                "message",
                "statusMessage",
                "localized",
            ),
        )
        if isinstance(percent, dict):
            completed = percent.get("completed")
            total = percent.get("total")
            if completed is not None and total:
                try:
                    percent = int((float(completed) / float(total)) * 100)
                except Exception:
                    percent = str(percent)
        return {
            "state": state or "UNKNOWN",
            "percent": percent if percent is not None else "UNKNOWN",
            "step": step or "UNKNOWN",
        }

    @staticmethod
    def _upgrade_complete(status):
        text = str(status).lower()
        return (
            (
                "complete" in text
                or "completed" in text
                or "success" in text
                or "succeeded" in text
                or "up_to_date" in text
            )
            and "failed" not in text
            and "error" not in text
        )

    @staticmethod
    def _upgrade_failed(status):
        if OpsPatchProvider._upgrade_status_unavailable(status):
            return False
        text = str(status).lower()
        return "failed" in text or "exception" in text or "fatal" in text
