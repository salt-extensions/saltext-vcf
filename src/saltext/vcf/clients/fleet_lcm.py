# pylint: disable=broad-exception-caught,consider-using-f-string,raise-missing-from
"""Fleet Lifecycle (``FLEET_LCM``) appliance upgrade client.

Fleet Lifecycle runs as its own service in the VCF Management Services cluster (its FQDN is
listed in VCF Operations under Build > Lifecycle > VCF Management > Components). VCF Operations
only brokers identity, so authentication goes to the VCF Operations FQDN and the ``/fleet-lcm``
calls go to the Fleet Lifecycle FQDN. Mirrors ``upgrade_fleet_lcm.sh``:

* ``POST <ops>/suite-api/api/auth/token/acquire``  - credentials, returns an OpsToken (``token``)
* ``POST <ops>/suite-api/api/auth/token/exchange`` - ``{"serviceKeys": ["fleet-lcm"]}``, returns ``jwtToken``
* ``GET  /fleet-lcm/v1/system``              - current state and ``availableTargetVersions``
* ``POST /fleet-lcm/v1/system``              - configure the upgrade plan, returns a task ``id``
* ``POST /fleet-lcm/v1/system?action=apply`` - apply the upgrade, returns a task ``id``
* ``POST /fleet-lcm/v1/depot-metadata?action=sync`` - sync the software depot metadata, returns a task ``id``
* ``GET  /fleet-lcm/v1/tasks/{id}``          - task ``status``
"""

import logging
import time

import requests
import urllib3

try:
    from salt.exceptions import CommandExecutionError
except Exception:

    class CommandExecutionError(Exception):
        pass


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RUNNING_STATES = ("IN_PROGRESS", "PENDING", "RUNNING")
SUCCESS_STATES = ("COMPLETED", "SUCCEEDED")


class FleetLcmError(CommandExecutionError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class FleetLcmClient:
    def __init__(
        self, host, ops_host, username, password, verify_ssl=False, timeout=300, logger=None
    ):
        self.log = logger or logging.getLogger(__name__)
        if not host:
            raise FleetLcmError("Fleet Lifecycle host (FQDN) is required")
        if not ops_host:
            raise FleetLcmError("VCF Operations host (FQDN) is required for token exchange")
        self.base_url = self._url(host)
        self.ops_url = self._url(ops_host)
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        self._token = None

    @staticmethod
    def _url(host):
        host = str(host)
        return host.rstrip("/") if host.startswith(("http://", "https://")) else f"https://{host}"

    def _ops_post(self, path, body, field, what, headers=None):
        try:
            response = self.session.post(
                self.ops_url + path,
                json=body,
                headers={"Accept": "application/json", **(headers or {})},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise FleetLcmError(f"VCF Operations {what} request failed: {exc}")
        value = None
        if response.ok:
            try:
                value = response.json().get(field)
            except (ValueError, AttributeError):
                pass
        if not value:
            raise FleetLcmError(
                "VCF Operations {} failed (HTTP {}). Check the VCF Operations FQDN and credentials.".format(
                    what, response.status_code
                ),
                status_code=response.status_code,
            )
        return value

    def authenticate(self):
        """Acquire an OpsToken, then exchange it for a ``fleet-lcm`` JWT."""
        ops_token = self._ops_post(
            "/suite-api/api/auth/token/acquire",
            {"username": self.username, "password": self.password},
            "token",
            "token acquire",
        )
        self._token = self._ops_post(
            "/suite-api/api/auth/token/exchange",
            {"serviceKeys": ["fleet-lcm"]},
            "jwtToken",
            "token exchange",
            headers={"Authorization": f"OpsToken {ops_token}"},
        )
        return self._token

    def request(self, method, path, body=None, _reauth=True):
        if not self._token:
            self.authenticate()
        try:
            response = self.session.request(
                method,
                self.base_url + path,
                json=body,
                headers={"Authorization": f"Bearer {self._token}", "Accept": "application/json"},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise FleetLcmError(f"Fleet Lifecycle API {method} {path} failed: {exc}")
        if response.status_code == 401 and _reauth:
            # The JWT expired or the identity service restarted (common mid-upgrade): get a fresh one.
            self.log.info("Fleet Lifecycle rejected the token (HTTP 401); acquiring a fresh one")
            self._token = None
            return self.request(method, path, body, _reauth=False)
        if response.status_code >= 400:
            raise FleetLcmError(
                "Fleet Lifecycle API {} {} failed. HTTP {}. Response: {}".format(
                    method, path, response.status_code, response.text
                ),
                status_code=response.status_code,
            )
        if not response.text.strip():
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def get_system(self):
        return self.request("GET", "/fleet-lcm/v1/system") or {}

    @staticmethod
    def available_versions(system):
        versions = []
        for item in (system or {}).get("availableTargetVersions") or []:
            version = item.get("targetVersion") if isinstance(item, dict) else item
            if version:
                versions.append(str(version))
        return versions

    @staticmethod
    def current_version(system):
        system = system or {}
        return system.get("currentVersion") or system.get("version")

    def select_target_version(self, system, requested=None):
        versions = self.available_versions(system)
        if requested:
            if versions and str(requested) not in versions:
                raise FleetLcmError(
                    "Target version {} is not available. Available: {}".format(
                        requested, ", ".join(versions)
                    )
                )
            return str(requested)
        if not versions:
            raise FleetLcmError(
                "No target versions found. Ensure the software depot metadata is synced."
            )
        return versions[0]

    def _submit(self, path, target_version):
        response = self.request("POST", path, {"targetVersion": target_version})
        task_id = response.get("id") if isinstance(response, dict) else None
        if not task_id:
            raise FleetLcmError(f"Fleet Lifecycle returned no task id for POST {path}: {response}")
        return task_id

    def configure_plan(self, target_version):
        return self._submit("/fleet-lcm/v1/system", target_version)

    def apply_upgrade(self, target_version):
        return self._submit("/fleet-lcm/v1/system?action=apply", target_version)

    def sync_depot_metadata(self):
        """Trigger a software depot metadata sync and return the task id."""
        path = "/fleet-lcm/v1/depot-metadata?action=sync"
        response = self.request("POST", path)
        task_id = response.get("id") if isinstance(response, dict) else None
        if not task_id:
            raise FleetLcmError(f"Fleet Lifecycle returned no task id for POST {path}: {response}")
        return task_id

    def wait_for_task(
        self, task_id, timeout_seconds=7200, poll_interval_seconds=15, sleep=time.sleep
    ):
        """Poll until the task leaves a running state; connection errors are retried (the appliance restarts)."""
        deadline = time.monotonic() + timeout_seconds
        status, response = "IN_PROGRESS", {}
        while status in RUNNING_STATES:
            if time.monotonic() >= deadline:
                raise FleetLcmError(f"Task {task_id} still {status} after {timeout_seconds}s")
            sleep(poll_interval_seconds)
            try:
                response = self.request("GET", f"/fleet-lcm/v1/tasks/{task_id}") or {}
                status = response.get("status") or "UNKNOWN"
            except FleetLcmError as exc:
                self.log.info("Fleet Lifecycle not reachable yet, retrying: %s", exc)
                status = "RUNNING"
                continue
            self.log.info("Fleet Lifecycle task %s status: %s", task_id, status)
        if status not in SUCCESS_STATES:
            raise FleetLcmError(f"Task {task_id} ended with status {status}: {response}")
        return {"task_id": task_id, "status": status, "task": response}
