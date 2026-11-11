# pylint: disable=broad-exception-caught
import hashlib
import os
import shutil
from urllib.parse import urlparse

try:
    from salt.exceptions import CommandExecutionError
except Exception:

    class CommandExecutionError(Exception):
        pass


def is_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def is_file_url(value):
    return isinstance(value, str) and value.startswith("file://")


def filename_from_source(source):
    parsed = urlparse(source)
    name = os.path.basename(parsed.path) if parsed.scheme else os.path.basename(source)
    return name or "VCF-Operations-upgrade.pak"


def sha256sum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_checksum(path, checksum):
    if not checksum:
        return None
    actual = sha256sum(path)
    if actual.lower() != str(checksum).lower():
        raise CommandExecutionError(
            f"Checksum mismatch for {path}. expected={checksum} actual={actual}"
        )
    return actual


def resolve_local_file(
    source,
    destination=None,
    download_dir="/tmp",
    requests_session=None,
    verify_ssl=False,
    timeout=1800,
    logger=None,
    checksum=None,
    calculate_checksum=False,
):
    if not source:
        raise CommandExecutionError("pak source is required")

    destination = destination or os.path.join(download_dir, filename_from_source(source))
    os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)

    if os.path.exists(destination):
        actual_checksum = _validate_checksum(destination, checksum)
        result = {
            "path": destination,
            "changed": False,
            "source": source,
            "already_present": True,
        }
        if calculate_checksum or checksum:
            result["sha256"] = actual_checksum or sha256sum(destination)
        return result

    if is_file_url(source):
        src_path = urlparse(source).path
        if not os.path.exists(src_path):
            raise CommandExecutionError(f"file:// source does not exist: {source}")
        shutil.copy2(src_path, destination)
        actual_checksum = _validate_checksum(destination, checksum)
        result = {"path": destination, "changed": True, "source": source}
        if calculate_checksum or checksum:
            result["sha256"] = actual_checksum or sha256sum(destination)
        return result

    if os.path.exists(source):
        if os.path.abspath(source) != os.path.abspath(destination):
            shutil.copy2(source, destination)
            changed = True
        else:
            changed = False
        actual_checksum = _validate_checksum(destination, checksum)
        result = {"path": destination, "changed": changed, "source": source}
        if calculate_checksum or checksum:
            result["sha256"] = actual_checksum or sha256sum(destination)
        return result

    if is_url(source):
        if requests_session is None:
            import requests

            requests_session = requests.Session()
            requests_session.trust_env = False
        if logger:
            logger.info("Downloading PAK from %s to %s", source, destination)
        with requests_session.get(
            source, stream=True, verify=verify_ssl, timeout=timeout
        ) as response:
            response.raise_for_status()
            with open(destination, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fh.write(chunk)
        actual_checksum = _validate_checksum(destination, checksum)
        result = {"path": destination, "changed": True, "source": source}
        if calculate_checksum or checksum:
            result["sha256"] = actual_checksum or sha256sum(destination)
        return result

    raise CommandExecutionError(f"Unsupported or missing PAK source: {source}")
