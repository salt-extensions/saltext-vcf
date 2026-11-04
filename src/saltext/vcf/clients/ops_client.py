# pylint: disable=broad-exception-caught,consider-using-f-string,subprocess-run-check,raise-missing-from
import json
import logging
import os
import shutil
import subprocess
from urllib.parse import urlparse

import requests
import urllib3

try:
    from salt.exceptions import CommandExecutionError
except Exception:

    class CommandExecutionError(Exception):
        pass


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OpsClient:
    """
    CASA/Admin API client for VCF Operations lifecycle.

    PAK install uses curl streaming multipart upload because CASA accepts this
    browser/curl-style multipart upload reliably for very large PAK files.
    The implementation does not use a shell and resolves curl by absolute path.
    """

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
        protocol = str(protocol or "https").strip().lower()
        if protocol not in ("http", "https"):
            protocol = "https"
        if str(host).startswith(("http://", "https://")):
            self.base_url = str(host).rstrip("/")
        else:
            self.base_url = f"{protocol}://{host}:{port}".rstrip("/")
        self.username = username
        self.password = password
        self.auth = (username, password)
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False

    def request(self, method, path, expected_status=(200,), **kwargs):
        url = path if str(path).startswith(("http://", "https://")) else self.base_url + path
        timeout = kwargs.pop("timeout", self.timeout)
        self.log.info("Calling VCF Operations API: method=%s url=%s", method, url)
        response = self.session.request(
            method=method,
            url=url,
            auth=self.auth,
            verify=self.verify_ssl,
            timeout=timeout,
            **kwargs,
        )
        if response.status_code not in expected_status:
            raise self._error(response, method, path)
        if not response.text or not response.text.strip():
            return None
        try:
            return response.json()
        except ValueError:
            return response.text.strip('"')

    @staticmethod
    def _error(response, method, path):
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        return CommandExecutionError(
            "VCF Operations API {} {} failed. HTTP {}. Response: {}".format(
                method, path, response.status_code, detail
            )
        )

    @staticmethod
    def _path_from_href(href):
        if not href:
            return None
        if href.startswith(("http://", "https://")):
            return urlparse(href).path
        return href

    @staticmethod
    def _curl_binary():
        candidates = []
        found = shutil.which("curl")
        if found:
            candidates.append(found)
        candidates.extend(("/usr/bin/curl", "/bin/curl", "/usr/local/bin/curl"))
        for candidate in candidates:
            if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        raise CommandExecutionError(
            f"curl executable not found or not executable. Checked: {candidates}"
        )

    def get_cluster_status(self):
        return self.request("GET", "/casa/cluster/status", expected_status=(200, 202))

    def get_cluster_nodes(self):
        return self.request("GET", "/casa/cluster/nodes", expected_status=(200, 202, 404, 500))

    def get_upgrade_status(self, pak_id=None, pak_status_path=None):
        errors, paths = [], []
        if pak_status_path:
            paths.append(self._path_from_href(pak_status_path))
        if pak_id:
            paths.append(f"/casa/upgrade/cluster/pak/{pak_id}/status")
        paths.extend(
            (
                "/casa/upgrade/cluster/status",
                "/casa/upgrade/status",
                "/casa/upgrade/cluster/pak/status",
                "/casa/upgrade/cluster/pak/reserved/status",
            )
        )
        seen = set()
        for path in paths:
            if not path or path in seen:
                continue
            seen.add(path)
            try:
                return {
                    "path": path,
                    "response": self.request("GET", path, expected_status=(200, 202)),
                }
            except Exception as exc:
                errors.append(str(exc))
        return {"path": None, "response": None, "errors": errors}

    def get_pak_status(self, pak_id=None, pak_status_path=None):
        """GET the status of one specific pak. Raises on any request error."""
        if pak_status_path:
            path = self._path_from_href(pak_status_path)
        elif pak_id:
            path = f"/casa/upgrade/cluster/pak/{pak_id}/status"
        else:
            raise CommandExecutionError("pak_id or pak_status_path is required")
        return {
            "path": path,
            "response": self.request("GET", path, expected_status=(200, 202)),
        }

    def get_system_status(self):
        errors = []
        for path in (
            "/casa/system/status",
            "/casa/cluster/status",
            "/suite-api/api/deployment/node/status",
        ):
            try:
                return {
                    "path": path,
                    "response": self.request("GET", path, expected_status=(200, 202)),
                }
            except Exception as exc:
                errors.append(str(exc))
        return {"path": None, "response": None, "errors": errors}

    def upload_and_install_pak(self, pak_file, pak_handling_advice="CLOBBER", timeout=7200):
        """
        Submit PAK to CASA silent_install.

        Uses curl streaming upload:
        - proven compatible with CASA large PAK uploads
        - no shell execution
        - absolute curl path
        - no Python multipart buffering
        """
        if not os.path.exists(pak_file):
            raise CommandExecutionError(f"PAK file does not exist: {pak_file}")
        if not os.path.isfile(pak_file):
            raise CommandExecutionError(f"PAK path is not a file: {pak_file}")
        curl_bin = self._curl_binary()
        path = "/casa/upgrade/cluster/pak/reserved/operation/silent_install"
        url = self.base_url + path
        file_size = os.path.getsize(pak_file)
        self.log.info("Submitting PAK to CASA silent_install API using curl streaming upload.")
        self.log.info("curl=%s", curl_bin)
        self.log.info(
            "PAK file=%s size=%s bytes handling_advice=%s", pak_file, file_size, pak_handling_advice
        )
        self.log.info(
            "silent_install POST can block for several minutes. After it returns, run vcf_ops_patch.wait_for_upgrade for progress polling."
        )
        cmd = [
            curl_bin,
            "--silent",
            "--show-error",
            "--write-out",
            "\\n%{http_code}",
            "--request",
            "POST",
            url,
            "--user",
            f"{self.username}:{self.password}",
            "--form",
            f"pak_handling_advice={pak_handling_advice}",
            "--form",
            f"contents=@{pak_file}",
            "--max-time",
            str(int(timeout)),
        ]
        if not self.verify_ssl:
            cmd.insert(1, "--insecure")
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "LANG": "C", "LC_ALL": "C"}
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(timeout) + 60,
                env=env,
                shell=False,
                close_fds=True,
            )
        except PermissionError as exc:
            raise CommandExecutionError(f"Unable to execute curl at {curl_bin}: {exc}")
        except Exception as exc:
            raise CommandExecutionError(f"curl silent_install execution failed: {exc}")
        stdout = proc.stdout or ""
        stderr = proc.stderr.strip() if proc.stderr else ""
        if proc.returncode != 0:
            raise CommandExecutionError(
                f"curl silent_install failed. rc={proc.returncode} stderr={stderr} stdout={stdout.strip()}"
            )
        lines = stdout.rstrip().splitlines()
        http_code = lines[-1].strip() if lines else ""
        body = "\n".join(lines[:-1]).strip() if len(lines) > 1 else ""
        if http_code not in ("200", "201", "202"):
            raise CommandExecutionError(
                "VCF Operations API POST {} failed. HTTP {}. Response: {}{}".format(
                    path, http_code, body, ("\nSTDERR: " + stderr) if stderr else ""
                )
            )
        self.log.info("CASA silent_install POST completed. HTTP=%s Response=%s", http_code, body)
        parsed = None
        if body:
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
        pak_status_path = None
        pak_id = None
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("rel") == "pak_cluster_status":
                    href = item.get("href")
                    pak_status_path = self._path_from_href(href)
                    parts = pak_status_path.strip("/").split("/") if pak_status_path else []
                    if "pak" in parts:
                        idx = parts.index("pak")
                        if len(parts) > idx + 1:
                            pak_id = parts[idx + 1]
        return {
            "http_code": http_code,
            "response": parsed,
            "pak_status_path": pak_status_path,
            "pak_id": pak_id,
            "file_size": file_size,
            "curl": curl_bin,
        }
