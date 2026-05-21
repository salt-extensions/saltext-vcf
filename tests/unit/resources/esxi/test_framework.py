"""Framework-interface tests for resources.esxi."""

from unittest.mock import MagicMock
from unittest.mock import patch

import responses

from saltext.vcf.resources import esxi as ex

KEY = ex.CONTEXT_KEY


def _fake_host(*, version="8.0.3", build="1234", vendor="Dell", services=()):
    """Build a SOAP-shaped HostSystem mock sufficient for esxi_host.info and esxi_service.list_."""
    host = MagicMock()
    host.summary.config.product.version = version
    host.summary.config.product.build = build
    host.summary.config.product.name = "VMware ESXi"
    host.summary.runtime.inMaintenanceMode = False
    host.summary.runtime.connectionState = "connected"
    host.summary.runtime.powerState = "poweredOn"
    host.hardware.systemInfo.vendor = vendor
    host.hardware.systemInfo.model = "R740"
    host.configManager.serviceSystem.serviceInfo.service = list(services)
    return host


def _service(key, *, running=True, policy="on"):
    svc = MagicMock()
    svc.key = key
    svc.label = key
    svc.running = running
    svc.policy = policy
    return svc


def test_discover(framework_opts):
    assert sorted(ex.discover(framework_opts)) == ["esxi-01", "esxi-02"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(ex, "__context__", ctx, raising=False)
    assert ex.initialized() is False
    ex.init(framework_opts)
    assert ex.initialized() is True
    assert "esxi-01" in ctx[KEY]["instances"]
    ex.shutdown(framework_opts)
    assert KEY not in ctx


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", json="tok", status=200)
    assert ex.ping() is True


def test_ping_failure(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", status=401)
    assert ex.ping() is False


def test_service_list(inject_resource_dunders, framework_opts):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    host = _fake_host(services=[_service("TSM-SSH", running=True, policy="on")])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = ex.service_list()
    assert "TSM-SSH" in result
    assert result["TSM-SSH"]["state"] == "RUNNING"


def test_ntp_set_servers(inject_resource_dunders, framework_opts):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    host = _fake_host()
    # esxi_ntp.set_servers re-reads to return the new state; stub QueryDateTimeInfo too.
    host.configManager.dateTimeSystem.QueryDateTimeInfo.return_value.ntpConfig.server = [
        "pool.ntp.org",
    ]
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        ex.ntp_set_servers(["pool.ntp.org"])
    call = host.configManager.dateTimeSystem.UpdateDateTimeConfig.call_args
    assert list(call.kwargs["config"].ntpConfig.server) == ["pool.ntp.org"]


def test_other_instance_targets_other_host(inject_resource_dunders, framework_opts):
    """Switching ``__resource__`` to esxi-02 routes opts at the second host."""
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-02", KEY, instances)
    host = _fake_host(version="8.0")
    captured = {}

    def fake_get_host_system(opts, profile=None):
        captured["host"] = opts["pillar"]["saltext.vcf"]["esxi"]["host"]
        return host

    with patch("saltext.vcf.utils.esxi.get_host_system", side_effect=fake_get_host_system):
        result = ex.host_info()
    assert captured["host"] == "esxi02.test"
    assert result["version"] == "8.0"


def test_grains_includes_host_info(inject_resource_dunders, framework_opts):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    host = _fake_host(version="8.0.3", build="1234", vendor="Dell")
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        g = ex.grains()
    assert g["resource_id"] == "esxi-01"
    assert g["resource_type"] == "esxi"
    assert g["version"] == "8.0.3"
    assert g["vendor"] == "Dell"
