# pylint: disable=broad-exception-caught,consider-using-f-string
try:
    from salt.exceptions import CommandExecutionError
except Exception:

    class CommandExecutionError(Exception):
        pass


def _pillar_get(salt_funcs, key, default=None):
    if salt_funcs and "pillar.get" in salt_funcs:
        return salt_funcs["pillar.get"](key, default or {})
    return default or {}


def as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "y", "on")


def as_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def clean_salt_kwargs(kwargs):
    return {k: v for k, v in (kwargs or {}).items() if not str(k).startswith("__")}


def get_vcenter_credentials(salt_funcs=None, overrides=None, required=True):
    overrides = clean_salt_kwargs(overrides or {})
    creds = dict(_pillar_get(salt_funcs, "vcenter", {}) or {})
    for source, target in {
        "vcenter": "host",
        "vc_host": "host",
        "host": "host",
        "username": "username",
        "password": "password",
        "protocol": "protocol",
        "port": "port",
        "verify_ssl": "verify_ssl",
        "timeout": "timeout",
        "use_service_account": "use_service_account",
    }.items():
        if source in overrides and overrides[source] is not None:
            creds[target] = overrides[source]
    creds.setdefault("protocol", "https")
    creds.setdefault("port", 443)
    creds.setdefault("verify_ssl", False)
    creds.setdefault("timeout", 300)
    creds.setdefault("use_service_account", False)
    if required:
        missing = []
        if not creds.get("host"):
            missing.append("vcenter.host")
        if not as_bool(creds.get("use_service_account"), False):
            if not creds.get("username"):
                missing.append("vcenter.username")
            if not creds.get("password"):
                missing.append("vcenter.password")
        if missing:
            raise CommandExecutionError(
                "Missing required vCenter credentials in pillar: {}".format(", ".join(missing))
            )
    return creds


def get_section(salt_funcs=None, section=None, default=None):
    return dict(_pillar_get(salt_funcs, section, default or {}) or {})


def get_ops_credentials(salt_funcs=None, overrides=None, required=True):
    overrides = clean_salt_kwargs(overrides or {})
    creds = dict(_pillar_get(salt_funcs, "ops", {}) or {})
    if not creds:
        creds = dict(_pillar_get(salt_funcs, "vcf_operations", {}) or {})
    if not creds:
        creds = dict(_pillar_get(salt_funcs, "vrops", {}) or {})
    for source, target in {
        "ops_host": "host",
        "vcf_operations": "host",
        "vrops": "host",
        "host": "host",
        "username": "username",
        "password": "password",
        "protocol": "protocol",
        "port": "port",
        "verify_ssl": "verify_ssl",
        "timeout": "timeout",
    }.items():
        if source in overrides and overrides[source] is not None:
            creds[target] = overrides[source]
    creds.setdefault("protocol", "https")
    creds.setdefault("port", 443)
    creds.setdefault("verify_ssl", False)
    creds.setdefault("timeout", 300)
    if required:
        missing = []
        if not creds.get("host"):
            missing.append("ops.host")
        if not creds.get("username"):
            missing.append("ops.username")
        if not creds.get("password"):
            missing.append("ops.password")
        if missing:
            raise CommandExecutionError(
                "Missing required VCF Operations credentials in pillar: {}".format(
                    ", ".join(missing)
                )
            )
    return creds
