"""Bounded SDDC Manager transport; never retry an ambiguous mutation."""

import logging
import time
from urllib.parse import urlsplit

import requests

try:
    from salt.exceptions import CommandExecutionError
except ImportError:

    class CommandExecutionError(Exception):
        """Execution failure when running outside Salt."""


class SddcConnectionError(CommandExecutionError):
    """A request failed before a usable HTTP response was received."""


class SddcHttpError(CommandExecutionError):
    """An HTTP failure with a status available to read-only polling policy."""

    def __init__(self, method, path, status_code):
        self.status_code = status_code
        super().__init__(f"SDDC Manager API {method} {path} failed: HTTP {status_code}")


def boolean(value, name="value"):
    """Accept Salt/CLI booleans without treating the string 'false' as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise CommandExecutionError(f"{name} must be a boolean")


def poll_settings(timeout, interval):
    timeout, interval = float(timeout), float(interval)
    if not (0 < timeout < float("inf") and 0 < interval < float("inf")):
        raise CommandExecutionError("Polling timeout and interval must be positive finite numbers")
    return time.monotonic() + timeout, interval


class SddcManagerClient:
    def __init__(
        self,
        host,
        username,
        password,
        protocol="https",
        port=443,
        verify_ssl=True,
        timeout=60,
        logger=None,
    ):
        self.log = logger or logging.getLogger(__name__)
        if not host or not username or not password:
            raise CommandExecutionError("host, username and password are required")
        self.base_url = (
            str(host).rstrip("/") if "://" in str(host) else f"{protocol}://{host}:{int(port)}"
        )
        url = urlsplit(self.base_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.path
            or url.query
            or url.fragment
        ):
            raise CommandExecutionError(
                "SDDC Manager host must be an HTTPS origin without credentials or path"
            )
        self.username = username
        self.password = password
        self.verify_ssl = boolean(verify_ssl, "verify_ssl")
        self.timeout = float(timeout)
        if not 0 < self.timeout < float("inf"):
            raise CommandExecutionError("HTTP timeout must be a positive finite number")
        self.session = requests.Session()
        self.session.trust_env = False
        self._token = None

    def authenticate(self, force=False):
        if self._token and not force:
            return self._token
        data = self._request_raw(
            "POST",
            "/v1/tokens",
            json={"username": self.username, "password": self.password},
            auth=False,
            expected=(200, 201),
        )
        token = data.get("accessToken") if isinstance(data, dict) else None
        if not token:
            raise CommandExecutionError("SDDC Manager token response did not contain accessToken")
        self._token = token
        return token

    def _request_raw(self, method, path, json=None, params=None, auth=True, expected=(200,)):
        if not str(path).startswith("/v1/") or "?" in path or "#" in path:
            raise CommandExecutionError("API path must be a relative /v1/ path")
        headers = {"Accept": "application/json"}
        if json is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(2):
            if auth:
                headers["Authorization"] = "Bearer " + self.authenticate(force=attempt == 1)
            self.log.debug("SDDC Manager API %s %s", method, path)
            try:
                response = self.session.request(
                    method,
                    self.base_url + path,
                    json=json,
                    params=params,
                    headers=headers,
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                    allow_redirects=False,
                )
            except requests.RequestException as exc:
                # Exception and response text can contain credentials; do not echo either.
                raise SddcConnectionError(
                    f"SDDC Manager API {method} {path} connection failed"
                ) from None
            if response.status_code == 401 and auth and attempt == 0:
                continue
            if response.status_code not in expected:
                raise SddcHttpError(method, path, response.status_code)
            if not response.text.strip():
                return {}
            try:
                data = response.json()
            except ValueError:
                raise CommandExecutionError(
                    f"SDDC Manager API {method} {path} returned invalid JSON"
                ) from None
            if not isinstance(data, dict):
                raise CommandExecutionError(
                    f"SDDC Manager API {method} {path} returned a non-object response"
                )
            return data

    def get(self, path, params=None, expected=(200,)):
        return self._request_raw("GET", path, params=params, expected=expected)

    def post(self, path, body=None, expected=(200, 201, 202)):
        return self._request_raw("POST", path, json=body, expected=expected)

    def patch(self, path, body=None, expected=(200, 202)):
        return self._request_raw("PATCH", path, json=body, expected=expected)

    def elements(self, path, params=None):
        """Read every page using VCF's zero-based page metadata."""
        params = dict(params or {})
        out = []
        page = 0
        while True:
            data = self.get(path, params=params or None)
            rows = data.get("elements")
            if not isinstance(rows, list):
                raise CommandExecutionError(f"Missing elements list in {path}")
            out.extend(rows)
            metadata = data.get("pageMetadata") or {}
            total = int(metadata.get("totalPages", 1))
            if page + 1 >= total:
                return out
            if not rows or int(metadata.get("pageNumber", page)) != page:
                raise CommandExecutionError(f"Invalid pagination in {path}")
            page += 1
            params["pageNumber"] = page

    def get_task(self, task_id):
        return self.get(f"/v1/tasks/{task_id}")

    def wait_task(self, task_id, timeout=3600, interval=30):
        deadline, interval = poll_settings(timeout, interval)
        while time.monotonic() < deadline:
            last = self.get_task(task_id)
            status = str(last.get("status", "UNKNOWN")).upper()
            if status in {"SUCCESSFUL", "COMPLETED_WITH_SUCCESS", "SUCCESS"}:
                return last
            if status in {
                "FAILED",
                "CANCELLED",
                "COMPLETED_WITH_FAILURE",
                "ERROR",
                "COMPLETED_WITH_WARNING",
            }:
                raise CommandExecutionError(f"SDDC task {task_id} ended with {status}")
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
        raise CommandExecutionError(f"Timed out waiting for SDDC task {task_id}")
