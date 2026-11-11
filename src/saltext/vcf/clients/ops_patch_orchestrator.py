# pylint: disable=broad-exception-caught,consider-using-f-string
import logging

try:
    from salt.exceptions import CommandExecutionError
except Exception:

    class CommandExecutionError(Exception):
        pass


class OpsPatchOrchestrator:
    def __init__(self, provider, logger=None):
        self.provider = provider
        self.log = logger or logging.getLogger(__name__)

    def cluster_health_validated(self, dry_run=False):
        status = self.provider.get_cluster_status()
        nodes = None
        try:
            nodes = self.provider.get_cluster_nodes()
        except Exception as exc:
            self.log.info("Cluster nodes API not available or failed: %s", exc)

        health = self.provider.cluster_health(status)
        if not health.get("healthy"):
            raise CommandExecutionError(
                "VCF Operations cluster is not healthy for upgrade: {}. Status: {}".format(
                    health.get("reason"),
                    status,
                )
            )

        return self._result(
            changed=False,
            success=True,
            comment="VCF Operations cluster health validated",
            data={
                "cluster_status": status,
                "nodes": nodes,
                "health": health,
            },
        )

    def pak_downloaded(
        self,
        pak_source,
        destination=None,
        download_dir="/tmp",
        download_timeout=1800,
        verify_download_ssl=False,
        checksum=None,
        calculate_checksum=False,
        dry_run=False,
    ):
        data = {
            "pak_source": pak_source,
            "destination": destination,
            "download_dir": download_dir,
            "checksum": checksum,
            "calculate_checksum": calculate_checksum,
        }

        if dry_run:
            return self._result(
                changed=True,
                success=True,
                comment="VCF Operations PAK would be downloaded/copied",
                data=data,
            )

        result = self.provider.resolve_pak_file(
            pak_source=pak_source,
            destination=destination,
            download_dir=download_dir,
            download_timeout=download_timeout,
            verify_ssl=verify_download_ssl,
            checksum=checksum,
            calculate_checksum=calculate_checksum,
        )
        changed = bool(result.get("changed"))
        return self._result(
            changed=changed,
            success=True,
            comment=(
                "VCF Operations PAK downloaded/copied"
                if changed
                else "VCF Operations PAK already present"
            ),
            data=result,
        )

    def pak_installed(
        self,
        pak_file,
        pak_handling_advice="CLOBBER",
        install_timeout=7200,
        dry_run=False,
        pak_id=None,
        force_content_update=True,
    ):
        """
        Upload the pak (unless Operations already has it) and start its install.

        With a known ``pak_id`` the pak's status on Operations decides what is
        needed: ``CANDIDATE`` skips the upload and only starts the install, an
        install that is already running or ``COMPLETED`` is left alone, and
        anything else uploads the pak again. A ``CANDIDATE`` pak whose pak_state
        shows the install already underway is not started a second time. A ``CANDIDATE`` pak whose content
        was never distributed (``NOT_DISTRIBUTED``, a stale record) is uploaded again too.
        """
        if not pak_file:
            raise CommandExecutionError("pak_file is required for install")

        data = {
            "pak_file": pak_file,
            "pak_handling_advice": pak_handling_advice,
            "install_response": None,
            "pak_id": pak_id,
            "pak_status_path": None,
            "uploaded": False,
            "install_triggered": False,
        }

        existing = self.provider.get_pak_install_status(pak_id) if pak_id and not dry_run else None
        if existing == "CANDIDATE" and self.provider.pak_content_missing(pak_id):
            existing = None
        elif existing == "CANDIDATE" and self.provider.pak_install_underway(pak_id):
            data["pak_status_path"] = f"/casa/upgrade/cluster/pak/{pak_id}/status"
            return self._result(
                changed=False,
                success=True,
                comment=f"VCF Operations pak {pak_id} install is already underway; not starting it again",
                data=data,
            )
        if existing and existing != "CANDIDATE" and existing != "FAILED":
            data["pak_status_path"] = f"/casa/upgrade/cluster/pak/{pak_id}/status"
            return self._result(
                changed=False,
                success=True,
                comment=f"VCF Operations pak {pak_id} is already {existing}; nothing to install",
                data=data,
            )

        if dry_run:
            return self._result(
                changed=True,
                success=True,
                comment="VCF Operations PAK install would be submitted",
                data=data,
            )

        if existing != "CANDIDATE":
            install_response = self.provider.upload_and_install_pak(
                pak_file=pak_file,
                pak_handling_advice=pak_handling_advice,
                timeout=install_timeout,
            )
            data["install_response"] = install_response
            data["uploaded"] = True
            if isinstance(install_response, dict):
                data["pak_id"] = install_response.get("pak_id") or data["pak_id"]
                data["pak_status_path"] = install_response.get("pak_status_path")
        if not data["pak_id"]:
            raise CommandExecutionError(
                "VCF Operations did not return a pak id after upload; cannot start the install"
            )
        if not data["pak_status_path"]:
            data["pak_status_path"] = f"/casa/upgrade/cluster/pak/{data['pak_id']}/status"

        self.provider.wait_for_pak_candidate(data["pak_id"])
        baseline = self.provider.get_pak_snapshot(data["pak_id"])
        try:
            self.provider.trigger_pak_install(
                data["pak_id"], force_content_update=force_content_update
            )
        except CommandExecutionError as exc:
            if not getattr(exc, "transient", False):
                raise
            self.log.warning(
                "VCF Operations install request ended with a gateway error (%s); checking whether it was accepted",
                exc,
            )
            started = self.provider.confirm_pak_install_started(data["pak_id"], baseline=baseline)
            if not started:
                raise
            data["install_note"] = "install request returned a gateway error; " + (
                "Operations was unreachable afterwards (it restarts during an upgrade), so the install is unconfirmed"
                if started[0] == "UNKNOWN"
                else f"the pak is now {started[0]} {list(started[1])}"
            )
        data["install_triggered"] = True

        return self._result(
            changed=True,
            success=True,
            comment="VCF Operations PAK install submitted",
            data=data,
        )

    def upgrade_monitored(
        self,
        timeout_seconds=14400,
        poll_interval_seconds=60,
        pak_id=None,
        pak_status_path=None,
        max_transient_errors=None,
    ):
        data = self.provider.wait_for_upgrade_completion(
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            pak_id=pak_id,
            pak_status_path=pak_status_path,
            max_transient_errors=max_transient_errors,
        )
        return self._result(
            changed=False,
            success=True,
            comment="VCF Operations upgrade completed",
            data=data,
        )

    def cluster_online_verified(self, timeout_seconds=7200, poll_interval_seconds=60):
        data = self.provider.wait_for_cluster_online(
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        return self._result(
            changed=False,
            success=True,
            comment="VCF Operations cluster is healthy/online",
            data=data,
        )

    def full_upgrade(
        self,
        pak_source,
        destination=None,
        pak_handling_advice="CLOBBER",
        download_dir="/tmp",
        download_timeout=1800,
        install_timeout=7200,
        monitor=True,
        upgrade_timeout_seconds=14400,
        cluster_online_timeout_seconds=7200,
        poll_interval_seconds=60,
        verify_download_ssl=False,
        validate_health=True,
        checksum=None,
        calculate_checksum=False,
        dry_run=False,
    ):
        data = {
            "cluster_health": None,
            "pak_download": None,
            "pak_install": None,
            "upgrade_monitor": None,
            "cluster_online": None,
            "report": None,
        }

        if validate_health:
            data["cluster_health"] = self.cluster_health_validated(dry_run=dry_run).get("data")

        data["pak_download"] = self.pak_downloaded(
            pak_source=pak_source,
            destination=destination,
            download_dir=download_dir,
            download_timeout=download_timeout,
            verify_download_ssl=verify_download_ssl,
            checksum=checksum,
            calculate_checksum=calculate_checksum,
            dry_run=dry_run,
        ).get("data")

        pak_file = (
            data["pak_download"].get("path")
            if isinstance(data["pak_download"], dict)
            else destination
        )

        data["pak_install"] = self.pak_installed(
            pak_file=pak_file,
            pak_handling_advice=pak_handling_advice,
            install_timeout=install_timeout,
            dry_run=dry_run,
        ).get("data")

        pak_id = None
        pak_status_path = None
        if isinstance(data["pak_install"], dict):
            pak_id = data["pak_install"].get("pak_id")
            pak_status_path = data["pak_install"].get("pak_status_path")

        if monitor and not dry_run:
            data["upgrade_monitor"] = self.upgrade_monitored(
                timeout_seconds=upgrade_timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
                pak_id=pak_id,
                pak_status_path=pak_status_path,
            ).get("data")
            data["cluster_online"] = self.cluster_online_verified(
                timeout_seconds=cluster_online_timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
            ).get("data")

        data["report"] = self.reported().get("data")
        return self._result(
            changed=True,
            success=True,
            comment="VCF Operations full upgrade flow completed/submitted",
            data=data,
        )

    def reported(self):
        return self._result(
            changed=False,
            success=True,
            comment="VCF Operations status collected",
            data={
                "cluster_status": self._safe(self.provider.get_cluster_status),
                "upgrade_status": self._safe(self.provider.get_upgrade_status),
                "system_status": self._safe(self.provider.get_system_status),
            },
        )

    @staticmethod
    def _safe(fn):
        try:
            return fn()
        except Exception as exc:
            return {"error": str(exc)}

    @staticmethod
    def _result(changed, success, comment, data):
        return {
            "changed": bool(changed),
            "success": bool(success),
            "result": bool(success),
            "comment": comment,
            "data": data or {},
            "changes": data or {} if changed else {},
        }
