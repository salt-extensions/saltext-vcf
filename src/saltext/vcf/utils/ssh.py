"""
SSH execution helper for appliance-local SDDC Manager controls.

Some SDDC Manager compliance controls have **no remote REST equivalent** — they
read appliance-local sources such as ``/etc/passwd`` or the unauthenticated
``http://localhost/appliancemanager`` API (see the ``mops`` config-modules
controllers ``local_os_users`` and ``password_policy``). To run these from a
Cloud Proxy / managing minion, this helper opens an SSH session to the
appliance and executes the command there.

Connection details are read from an ``ssh`` sub-block of the component config,
e.g. ``saltext.vcf.sddc_manager.ssh``:

.. code-block:: yaml

    saltext.vcf:
      sddc_manager:
        host: sddc-manager.example.test     # REST host
        ssh:
          host: sddc-manager.example.test   # optional; defaults to the REST host
          username: vcf
          password: secret
          port: 22                          # optional, default 22

No privilege escalation is needed for the controls that use this helper:
``/etc/passwd`` is world-readable and the appliancemanager API is reachable on
localhost without authentication (the "zero sudo" design of the on-appliance
controls).
"""

import logging

log = logging.getLogger(__name__)

DEFAULT_PORT = 22
DEFAULT_TIMEOUT = 30


def run(ssh_cfg, command, timeout=DEFAULT_TIMEOUT):
    """Execute *command* on the remote host over SSH.

    :param ssh_cfg: Dict with keys ``host``, ``username``, ``password`` and
        optional ``port`` (see :func:`saltext.vcf.utils.sddc.get_ssh_config`).
    :param command: Shell command to run on the appliance.
    :param timeout: Connect / exec timeout in seconds.
    :return: Tuple ``(returncode, stdout, stderr)`` with text output.
    :raises RuntimeError: if paramiko is unavailable or the connection fails.
    """
    try:
        import paramiko  # bundled with Salt (salt-ssh dependency)
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "paramiko is required for SSH-based SDDC Manager controls but is not importable"
        ) from exc

    host = ssh_cfg.get("host")
    if not host:
        raise RuntimeError("SSH config is missing a 'host'")

    class _FIPSAcceptPolicy(paramiko.MissingHostKeyPolicy):
        # AutoAddPolicy.missing_host_key() calls get_fingerprint() which uses MD5.
        # MD5 is disabled in FIPS mode — this policy accepts without fingerprinting.
        def missing_host_key(self, client, hostname, key):
            pass

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(_FIPSAcceptPolicy())
    try:
        client.connect(
            hostname=host,
            port=ssh_cfg.get("port", DEFAULT_PORT),
            username=ssh_cfg.get("username"),
            password=ssh_cfg.get("password"),
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
    except Exception as exc:  # noqa: BLE001 - surface any connect failure uniformly
        raise RuntimeError(f"SSH connection to {host} failed: {exc}") from exc

    try:
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        rc = stdout.channel.recv_exit_status()
        log.debug("ssh %s rc=%s cmd=%r", host, rc, command)
        return rc, out, err
    finally:
        client.close()
