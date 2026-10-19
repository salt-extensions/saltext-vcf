"""Regression tests for API payloads, fail-closed execution and safe resume."""

import json
from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests
from saltext.vcf.clients import vcf_upgrade as api
from saltext.vcf.modules import vcf_upgrade as execution
from saltext.vcf.states import vcf_upgrade as states
from saltext.vcf.utils import vcf_upgrade_orchestrator as orchestration
from saltext.vcf.utils import vcf_upgrade_transport as transport

ERROR = transport.CommandExecutionError


@pytest.fixture
def provider():
    obj = api.VcfUpgradeProvider("manager.test", "user", "secret")
    obj.client = Mock(base_url="https://manager.test")
    return obj


def bundle(version="9.1.0-123", status="SUCCESSFUL", component="SDDC_MANAGER", bid="bundle-1"):
    return {
        "id": bid,
        "version": version,
        "downloadStatus": status,
        "components": [{"type": component, "toVersion": "9.1.0.0-456"}],
    }


def response(status=200, data=None, text=None):
    obj = Mock(status_code=status)
    obj.text = json.dumps(data or {}) if text is None else text
    obj.json.return_value = data or {}
    return obj


def test_transport_refreshes_token_once_and_disables_redirects():
    obj = transport.SddcManagerClient("manager.test", "u", "secret")
    obj.session.request = Mock(
        side_effect=[
            response(data={"accessToken": "first"}),
            response(401),
            response(data={"accessToken": "second"}),
            response(data={"id": "ok"}),
        ]
    )
    assert obj.get("/v1/domains")["id"] == "ok"
    calls = obj.session.request.call_args_list
    assert len(calls) == 4
    assert all(call.kwargs["allow_redirects"] is False for call in calls)
    assert calls[-1].kwargs["headers"]["Authorization"] == "Bearer second"


def test_transport_does_not_expose_error_response_or_retry_ambiguous_post():
    obj = transport.SddcManagerClient("manager.test", "u", "secret")
    obj._token = "token"
    obj.session.request = Mock(return_value=response(500, text="password=secret"))
    with pytest.raises(ERROR) as exc:
        obj.post("/v1/upgrades", {})
    assert "secret" not in str(exc.value)
    assert obj.session.request.call_count == 1
    obj.session.request.side_effect = requests.ConnectionError("password=secret")
    with pytest.raises(transport.SddcConnectionError) as exc:
        obj.post("/v1/upgrades", {})
    assert "secret" not in str(exc.value)


def test_retry_connection_failure_is_wrapped():
    obj = transport.SddcManagerClient("manager.test", "u", "secret")
    obj._token = "old"
    obj.session.request = Mock(
        side_effect=[
            response(401),
            response(data={"accessToken": "new"}),
            requests.ConnectionError("secret"),
        ]
    )
    with pytest.raises(transport.SddcConnectionError):
        obj.get("/v1/domains")


@pytest.mark.parametrize(
    "host", ["http://manager.test", "https://u:p@manager.test", "https://manager.test/path"]
)
def test_invalid_origins_rejected(host):
    with pytest.raises(ERROR):
        transport.SddcManagerClient(host, "u", "secret")


def test_tls_and_false_string():
    assert transport.SddcManagerClient("manager.test", "u", "p").verify_ssl is True
    assert (
        transport.SddcManagerClient("manager.test", "u", "p", verify_ssl="false").verify_ssl
        is False
    )


def test_invalid_json_and_absolute_paths_rejected():
    obj = transport.SddcManagerClient("manager.test", "u", "secret")
    obj._token = "token"
    obj.session.request = Mock(return_value=response())
    obj.session.request.return_value.json.side_effect = ValueError()
    with pytest.raises(ERROR, match="invalid JSON"):
        obj.get("/v1/domains")
    with pytest.raises(ERROR, match="relative"):
        obj.get("https://other.test/v1/domains")


def test_pagination():
    obj = transport.SddcManagerClient("manager.test", "u", "secret")
    obj.get = Mock(
        side_effect=[
            {"elements": [1], "pageMetadata": {"pageNumber": 0, "totalPages": 2}},
            {"elements": [2], "pageMetadata": {"pageNumber": 1, "totalPages": 2}},
        ]
    )
    assert obj.elements("/v1/bundles") == [1, 2]
    assert obj.get.call_args.kwargs["params"] == {"pageNumber": 1}


def test_detect_current_release_uses_releases_api(provider):
    provider.client.elements.return_value = [{"version": "9.0.2.0"}]
    assert provider.current_domain_version("domain-1") == "9.0.2.0"
    provider.client.elements.assert_called_once_with("/v1/releases", {"domainId": "domain-1"})


def test_release_selection(provider):
    provider.client.elements.return_value = [
        {"version": v, "bom": [{"name": "SDDC_MANAGER"}]} for v in ["9.0.1.0", "9.0.3.0", "9.1.0.0"]
    ]
    assert provider.list_target_versions(domain_id="domain-1", current_version="9.0.2.0") == [
        "9.1.0.0"
    ]


def test_patch_precision_and_exact_build():
    assert api._version_match("9.1.0.0", "9.1.0-123")
    assert not api._version_match("9.1.0.1", "9.1.0.2-123")
    assert not api._version_match("9.1.0-1", "9.1.0-2")


def test_bundle_ambiguity_includes_not_yet_downloaded_builds(provider):
    provider.client.elements.return_value = [bundle(), bundle("9.1.0-999", "AVAILABLE")]
    with pytest.raises(ERROR, match="Multiple"):
        provider.find_bundle("SDDC_MANAGER", "9.1.0", "SUCCESSFUL")


def test_duplicate_identical_bundle_rows_are_safe(provider):
    provider.client.elements.return_value = [bundle(), bundle()]
    assert provider.find_bundle("SDDC_MANAGER", "9.1.0")["id"] == "bundle-1"


def test_different_ids_with_same_version_are_ambiguous(provider):
    provider.client.elements.return_value = [bundle(), bundle(bid="bundle-2")]
    with pytest.raises(ERROR, match="Multiple bundle IDs"):
        provider.find_bundle("SDDC_MANAGER", "9.1.0")


@pytest.mark.parametrize("status", ["SUCCESSFUL", "IN_PROGRESS", "SCHEDULED"])
def test_download_does_not_retrigger_existing_or_active_bundle(provider, status):
    provider.client.elements.return_value = [bundle(status=status)]
    assert provider.ensure_bundle_download("SDDC_MANAGER", "9.1.0")["changed"] is False
    provider.client.patch.assert_not_called()


def test_download_patch_payload(provider):
    provider.client.elements.return_value = [bundle(status="AVAILABLE")]
    assert provider.ensure_bundle_download("SDDC_MANAGER", "9.1.0")["changed"]
    provider.client.patch.assert_called_once_with(
        "/v1/bundles/bundle-1", {"bundleDownloadSpec": {"downloadNow": True}}
    )


@pytest.mark.parametrize("component", ["SDDC_MANAGER", "NSX_T_MANAGER", "VCENTER", "HOST"])
def test_create_payloads(provider, component):
    provider.client.get.side_effect = lambda path: (
        {"domain": {"id": "domain-1"}}
        if "clusters" in path
        else {"nsxtCluster": {"vipFqdn": "nsx.test"}}
    )
    provider.client.post.return_value = {
        "id": "task-1",
        "resources": [{"type": "UPGRADE_ID", "resourceId": "upgrade-1"}],
    }
    options = (
        {"cluster_id": "cluster-1", "personality_id": "personality-1"}
        if component == "HOST"
        else {}
    )
    result = provider.create_upgrade("domain-1", "bundle-1", "9.1.0-123", component, **options)
    assert result["upgradeId"] == "upgrade-1"
    path, payload = provider.client.post.call_args.args
    assert path == "/v1/upgrades"
    assert payload["resourceType"] == ("CLUSTER" if component == "HOST" else "DOMAIN")
    assert payload["draftMode"] is (component != "SDDC_MANAGER")
    if component == "SDDC_MANAGER":
        assert payload["resourceUpgradeSpecs"][0]["upgradeNow"] is True
        assert payload["resourceUpgradeSpecs"][0]["toVersion"] == "9.1.0-123"
    elif component == "NSX_T_MANAGER":
        assert payload["nsxtUpgradeUserInputSpecs"][0]["nsxtId"] == "nsx.test"
    elif component == "VCENTER":
        assert payload["vcenterUpgradeUserInputSpecs"] == [
            {"resourceId": "domain-1", "upgradeMechanism": "InPlace"}
        ]
    else:
        assert (
            payload["resourceUpgradeSpecs"][0]["personalitySpec"]["personalityId"]
            == "personality-1"
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"component_type": "INVALID"},
        {"draft_mode": True},
        {"component_type": "NSX_T_MANAGER", "draft_mode": False},
        {"schedule_for_later": True},
        {"component_type": "HOST"},
    ],
)
def test_create_invalid_arguments_never_submit(provider, kwargs):
    with pytest.raises(ERROR):
        provider.create_upgrade("domain-1", "bundle-1", "9.1.0-123", **kwargs)
    provider.client.post.assert_not_called()


def test_scheduled_creation(provider):
    provider.client.post.return_value = {"id": "upgrade-1"}
    provider.create_upgrade(
        "domain-1",
        "bundle-1",
        "9.1.0-123",
        schedule_for_later=True,
        scheduled_timestamp="2030-01-01T00:00:00Z",
    )
    spec = provider.client.post.call_args.args[1]["resourceUpgradeSpecs"][0]
    assert spec["upgradeNow"] is False
    assert spec["scheduledTimestamp"] == "2030-01-01T00:00:00Z"


def test_execute_is_idempotent_and_rejects_failure(provider):
    provider.client.get.return_value = {"status": "IN_PROGRESS"}
    assert provider.execute_upgrade("upgrade-1")["changed"] is False
    provider.client.patch.assert_not_called()
    provider.client.get.return_value = {"status": "FAILED"}
    with pytest.raises(ERROR):
        provider.execute_upgrade("upgrade-1")


@pytest.mark.parametrize("component", ["NSX_T_MANAGER", "VCENTER", "HOST"])
def test_precheck_selects_checks_and_component_specific_context(provider, component):
    provider.client.get.side_effect = (
        [
            bundle(component=component),
            {"nsxtCluster": {"vipFqdn": "nsx.test"}, "vcenters": [{"fqdn": "vc.test"}]},
        ]
        if component != "HOST"
        else [bundle(component=component)]
    )
    provider.client.post.side_effect = [
        {
            "queryId": "query-1",
            "resources": [
                {
                    "resourceId": "resource-1",
                    "resourceType": component,
                    "resourceName": "test",
                    "checkSets": [{"checkSetId": "check-1"}],
                }
            ],
        },
        {"id": "run-1"},
    ]
    assert (
        provider.start_precheck("upgrade-1", "domain-1", "bundle-1", component)["checkSetId"]
        == "run-1"
    )
    payload = provider.client.post.call_args.args[1]
    assert payload["resources"][0]["checkSets"] == [{"checkSetId": "check-1"}]
    if component == "HOST":
        assert payload["metadata"]["upgradeId"] == "upgrade-1"
        assert "contextVariables" not in payload
    else:
        assert payload["contextVariables"] == {"upgradeId": "upgrade-1"}


@pytest.mark.parametrize(
    "data",
    [
        {"status": "FAILED"},
        {"status": "SUCCESSFUL"},
        {
            "validationResult": {
                "nestedErrors": [{"notifications": [{"severity": "ERROR", "message": "failed"}]}]
            }
        },
        {
            "validationResult": {},
            "presentedArtifactsMap": {"validation-domain-summary": [{"criticalGapsCount": 1}]},
        },
    ],
)
def test_precheck_failure_blocks_upgrade(provider, data):
    provider.client.get.return_value = data
    with pytest.raises(ERROR, match="failed"):
        provider.wait_precheck("run-1", timeout=1, interval=0.01)


def test_partial_validation_does_not_mean_finished(provider):
    provider.client.get.return_value = {"status": "IN_PROGRESS", "validationResult": {}}
    assert provider.precheck_status("run-1")["isFinished"] is False


@pytest.mark.parametrize(
    "status", ["FAILED", "CANCELLED", "COMPLETED_WITH_FAILURE", "COMPLETED_WITH_WARNING", "SKIPPED"]
)
def test_terminal_upgrade_failure(provider, status):
    provider.client.get.return_value = {"status": status}
    with pytest.raises(ERROR, match=status):
        provider.wait_upgrade("upgrade-1", timeout=1, interval=0.01)


@pytest.mark.parametrize("timeout,interval", [(0, 1), (1, 0), (-1, 1), (float("nan"), 1)])
def test_invalid_polling_rejected(provider, timeout, interval):
    with pytest.raises(ERROR):
        provider.wait_upgrade("upgrade-1", timeout, interval)


def test_postcondition_checks_component_build(provider):
    provider.client.get.side_effect = [{"status": "ACTIVE"}, bundle()]
    provider.client.elements.return_value = [
        {"domain": {"id": "domain-1"}, "version": "9.1.0.0-000"}
    ]
    assert (
        provider.validate_post_upgrade("domain-1", "SDDC_MANAGER", bundle_id="bundle-1")["healthy"]
        is False
    )


@pytest.fixture
def workflow(provider, tmp_path):
    provider.find_bundle = Mock(return_value=bundle())
    provider.management_domain_id = Mock(return_value="domain-1")
    provider.plan = Mock(
        return_value={"domainId": "domain-1", "bundleId": "bundle-1", "targetVersion": "9.1.0-123"}
    )
    provider.create_upgrade = Mock(
        spec=provider.create_upgrade,
        return_value={"upgradeId": "upgrade-1", "draftModeUsed": False},
    )
    # Preserve the real signature, used to validate options before mutations.
    provider.build_upgrade_payload = Mock(return_value={})
    provider.wait_upgrade = Mock(return_value={"upgradeStatus": "COMPLETED_WITH_SUCCESS"})
    provider.validate_post_upgrade = Mock(return_value={"healthy": True})
    provider.wait_draft = Mock()
    provider.start_precheck = Mock(return_value={"checkSetId": "run-1"})
    provider.wait_precheck = Mock(return_value={"failed": False})
    provider.execute_upgrade = Mock(return_value={"changed": True})
    orch = orchestration.VcfUpgradeOrchestrator(
        provider, checkpoint_file=str(tmp_path / "checkpoint.json")
    )
    return orch, provider


def test_single_component_runs_and_rerun_skips(workflow):
    orch, obj = workflow
    assert orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")["changed"] is True
    assert orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")["changed"] is False
    obj.create_upgrade.assert_called_once()
    assert obj.validate_post_upgrade.call_count == 2


def test_resume_after_monitor_failure_reuses_upgrade_id(workflow):
    orch, obj = workflow
    obj.wait_upgrade.side_effect = ERROR("interrupted")
    with pytest.raises(ERROR):
        orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    obj.wait_upgrade.side_effect = None
    assert orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")["changed"] is False
    obj.create_upgrade.assert_called_once()


def test_unknown_creation_outcome_requires_reconciliation(workflow):
    orch, obj = workflow
    obj.create_upgrade.side_effect = transport.SddcConnectionError("lost response")
    with pytest.raises(ERROR):
        orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    with pytest.raises(ERROR, match="outcome is unknown"):
        orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    obj.create_upgrade.assert_called_once()


def test_checkpoint_rejects_changed_target_and_corruption(workflow):
    orch, obj = workflow
    orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    with pytest.raises(ERROR, match="different"):
        orch.full_upgrade("SDDC_MANAGER", "9.2.0-999")
    with open(orch.checkpoint_file, "w") as stream:
        stream.write("{")
    with pytest.raises(ERROR, match="Cannot read checkpoint"):
        orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    obj.create_upgrade.assert_called_once()


def test_create_only_draft_then_resume_full_workflow(workflow):
    orch, obj = workflow
    obj.create_upgrade.return_value["draftModeUsed"] = True
    seq = [{"type": "NSX_T_MANAGER"}]
    assert orch.sequence(seq, "9.1.0-123", create_only=True)["changed"]
    obj.execute_upgrade.assert_not_called()
    assert orch.sequence(seq, "9.1.0-123")["changed"]
    obj.create_upgrade.assert_called_once()
    obj.start_precheck.assert_called_once()
    obj.execute_upgrade.assert_called_once()


def test_failed_precheck_never_executes_or_recreates(workflow):
    orch, obj = workflow
    obj.create_upgrade.return_value["draftModeUsed"] = True
    obj.wait_precheck.side_effect = ERROR("precheck failed")
    for _ in range(2):
        with pytest.raises(ERROR, match="precheck failed"):
            orch.full_upgrade("NSX_T_MANAGER", "9.1.0-123")
    obj.execute_upgrade.assert_not_called()
    obj.create_upgrade.assert_called_once()
    obj.start_precheck.assert_called_once()


def test_all_sequence_specs_validated_before_creation(workflow):
    orch, obj = workflow
    with pytest.raises(ERROR, match="HOST requires"):
        orch.sequence(["SDDC_MANAGER", "HOST"], "9.1.0-123")
    obj.create_upgrade.assert_not_called()


def test_host_expansion_discards_display_name_and_keeps_cluster_identity(workflow):
    orch, obj = workflow
    result = orch._expand(
        [
            {
                "type": "HOST",
                "clusters": [{"name": "friendly", "cluster_id": "c-1", "personality_id": "p-1"}],
            }
        ],
        "9.1.0-123",
        "domain-1",
    )
    assert result[0]["name"] == "HOST:c-1"
    assert "name" not in result[0]["options"]


def test_dry_run_does_not_write_checkpoint_or_submit(workflow):
    orch, obj = workflow
    assert orch.full_upgrade("SDDC_MANAGER", "9.1.0-123", dry_run=True)["changed"]
    assert not __import__("pathlib").Path(orch.checkpoint_file).exists()
    obj.create_upgrade.assert_not_called()


def test_checkpoint_lock_prevents_concurrent_mutation(workflow):
    orch, obj = workflow
    other = orchestration.VcfUpgradeOrchestrator(obj, checkpoint_file=orch.checkpoint_file)
    with orch._lock():
        with pytest.raises(ERROR, match="Another upgrade"):
            other.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    obj.create_upgrade.assert_not_called()


def test_state_test_mode_reports_none_and_does_not_monitor(monkeypatch):
    called = Mock(return_value={"changed": True, "comment": "would change", "data": {"id": "plan"}})
    monitor = Mock()
    monkeypatch.setattr(states, "__opts__", {"test": True}, raising=False)
    monkeypatch.setattr(
        states,
        "__salt__",
        {"vcf_upgrade.run": called, "vcf_upgrade.wait_for_upgrade": monitor},
        raising=False,
    )
    assert states.upgraded("test")["result"] is None
    assert called.call_args.kwargs["dry_run"] is True
    assert states.upgrade_monitored("test", "upgrade-1")["result"] is None
    monitor.assert_not_called()


def test_execution_run_is_wired_to_workflow(monkeypatch, workflow):
    orch, obj = workflow
    monkeypatch.setattr(execution, "_orch", lambda *a, **kw: orch)
    monkeypatch.setattr(execution, "_u", lambda: {"target_build": "9.1.0-123"})
    assert execution.run()["changed"] is True
    obj.create_upgrade.assert_called_once()


class SimulatedSddc:
    """Exercise the real transport/provider/orchestrator together without network calls."""

    def __init__(self):
        self.upgrades = {}
        self.prechecked = set()
        self.calls = []
        self.components = ["SDDC_MANAGER", "NSX_T_MANAGER", "VCENTER", "HOST"]

    def request(self, method, url, **kwargs):
        from urllib.parse import urlsplit

        path = urlsplit(url).path
        body = kwargs.get("json")
        self.calls.append((method, path, deepcopy(body)))
        if path == "/v1/tokens":
            return response(data={"accessToken": "test-token"})
        assert kwargs["headers"]["Authorization"] == "Bearer test-token"
        if method == "GET":
            if path == "/v1/domains":
                return response(data={"elements": [{"id": "domain-1", "type": "MANAGEMENT"}]})
            if path == "/v1/domains/domain-1":
                return response(
                    data={
                        "id": "domain-1",
                        "status": "ACTIVE",
                        "nsxtCluster": {"id": "nsx-1", "vipFqdn": "nsx.test"},
                        "vcenters": [{"id": "vc-1", "fqdn": "vc.test"}],
                    }
                )
            if path == "/v1/bundles":
                return response(
                    data={"elements": [bundle(component=c, bid=c) for c in self.components]}
                )
            if path.startswith("/v1/bundles/"):
                ctype = path.rsplit("/", 1)[-1]
                return response(data=bundle(component=ctype, bid=ctype))
            if path == "/v1/clusters/cluster-1":
                return response(
                    data={
                        "domain": {"id": "domain-1"},
                        "status": "ACTIVE",
                        "hosts": [{"id": "host-1"}],
                    }
                )
            if path == "/v1/hosts/host-1":
                return response(
                    data={"esxiVersion": "9.1.0-0.0.456", "configurationStatus": "ACTIVE"}
                )
            if path == "/v1/nsxt-clusters/nsx-1":
                return response(data={"version": "9.1.0.0-456", "status": "STABLE"})
            if path == "/v1/vcenters/vc-1":
                return response(data={"version": "9.1.0.0-456"})
            if path == "/v1/sddc-managers":
                return response(
                    data={"elements": [{"domain": {"id": "domain-1"}, "version": "9.1.0.0-456"}]}
                )
            if path.startswith("/v1/upgrades/"):
                return response(data=self.upgrades[path.rsplit("/", 1)[-1]])
            if path.startswith("/v1/system/check-sets/run-"):
                return response(data={"status": "COMPLETED", "validationResult": {}})
        if method == "POST":
            if path == "/v1/upgrades":
                uid = "upgrade-" + str(len(self.upgrades))
                self.upgrades[uid] = {
                    "id": uid,
                    "status": "DRAFT" if body["draftMode"] else "COMPLETED_WITH_SUCCESS",
                }
                return response(
                    202, {"id": uid, "resources": [{"type": "UPGRADE_ID", "resourceId": uid}]}
                )
            if path == "/v1/system/check-sets/queries":
                return response(
                    data={
                        "queryId": "query-1",
                        "resources": [
                            {
                                "resourceId": "resource-1",
                                "resourceName": "test",
                                "resourceType": "HOST",
                                "checkSets": [{"checkSetId": "selected-1"}],
                            }
                        ],
                    }
                )
            if path == "/v1/system/check-sets":
                assert body["resources"][0]["checkSets"] == [{"checkSetId": "selected-1"}]
                uid = body.get("contextVariables", body["metadata"])["upgradeId"]
                self.prechecked.add(uid)
                return response(202, {"id": "run-1"})
        if method == "PATCH" and path.startswith("/v1/upgrades/"):
            uid = path.rsplit("/", 1)[-1]
            assert uid in self.prechecked, "Draft execution must follow prechecks"
            self.upgrades[uid]["status"] = "COMPLETED_WITH_SUCCESS"
            return response(data=self.upgrades[uid])
        raise AssertionError(f"Unexpected API request: {method} {path}")


def test_real_transport_whole_sequence_and_idempotent_rerun(tmp_path):
    server = SimulatedSddc()
    obj = api.VcfUpgradeProvider("manager.test", "u", "p")
    obj.client.session.request = server.request
    orch = orchestration.VcfUpgradeOrchestrator(
        obj, checkpoint_file=str(tmp_path / "checkpoint.json")
    )
    sequence = [
        "SDDC_MANAGER",
        "NSX_T_MANAGER",
        "VCENTER",
        {
            "type": "HOST",
            "clusters": [
                {"name": "management", "cluster_id": "cluster-1", "personality_id": "image-1"}
            ],
        },
    ]
    assert orch.sequence(sequence, "9.1.0-123")["changed"] is True
    assert len(server.upgrades) == 4
    assert len(server.prechecked) == 3
    assert orch.sequence(sequence, "9.1.0-123")["changed"] is False
    assert (
        sum(method == "POST" and path == "/v1/upgrades" for method, path, body in server.calls) == 4
    )
    checkpoint = json.loads((tmp_path / "checkpoint.json").read_text())
    assert all(c["phase"] == "COMPLETED" for c in checkpoint["components"].values())
    assert "password" not in (tmp_path / "checkpoint.json").read_text()


def test_inventory_version_layouts():
    assert api._version_match("9.1.0.0-456", "9.1.0-0.0.456")
    assert api._version_match("9.1.0-456", "9.1.0.0.456")
    assert not api._version_match("9.1.0-456", "9.1.0.0.999")


def test_postcondition_rejects_unhealthy_domain_even_with_matching_version(provider):
    provider.client.get.side_effect = [{"status": "ERROR"}, bundle()]
    provider.client.elements.return_value = [{"domain": {"id": "domain-1"}, "version": "9.1.0-456"}]
    assert not provider.validate_post_upgrade("domain-1", "SDDC_MANAGER", bundle_id="bundle-1")[
        "healthy"
    ]


def test_incomplete_reset_rejected(workflow):
    orch, obj = workflow
    obj.wait_upgrade.side_effect = ERROR("monitor interrupted")
    with pytest.raises(ERROR):
        orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    with pytest.raises(ERROR, match="Cannot reset"):
        orch.sequence(["SDDC_MANAGER"], "9.1.0-123", reset_checkpoint=True)
    obj.create_upgrade.assert_called_once()


def test_missing_selected_checks_never_triggers_run(provider):
    provider.client.get.side_effect = [
        bundle(component="VCENTER"),
        {"vcenters": [{"fqdn": "vc.test"}]},
    ]
    provider.client.post.return_value = {"queryId": "q", "resources": [{"resourceId": "vc-1"}]}
    with pytest.raises(ERROR, match="no selectable checks"):
        provider.start_precheck("u-1", "domain-1", "bundle-1", "VCENTER")
    assert provider.client.post.call_count == 1


def test_state_dry_run_false_string_does_not_mask_live_result(monkeypatch):
    called = Mock(return_value={"changed": True, "comment": "changed", "data": {"id": "u-1"}})
    monkeypatch.setattr(states, "__opts__", {"test": False}, raising=False)
    monkeypatch.setattr(states, "__salt__", {"vcf_upgrade.run": called}, raising=False)
    assert states.upgraded("test", dry_run="false")["result"] is True
    assert called.call_args.kwargs["dry_run"] is False


def test_native_pillar_and_profile_configuration(monkeypatch):
    opts = {
        "pillar": {
            "saltext.vcf": {
                "sddc_manager": {"host": "default.test", "username": "u", "password": "p"},
                "profiles": {
                    "other": {
                        "sddc_manager": {
                            "host": "other.test",
                            "username": "u2",
                            "password": "p2",
                            "port": 8443,
                        }
                    }
                },
                "vcf_upgrade": {"target_build": "9.1.0-123"},
            }
        },
        "cachedir": "/tmp/salt-cache",
    }
    monkeypatch.setattr(execution, "__opts__", opts, raising=False)
    assert execution._provider().client.base_url == "https://default.test:443"
    assert execution._provider(profile="other").client.base_url == "https://other.test:8443"
    assert execution._u()["target_build"] == "9.1.0-123"
    assert execution._orch().checkpoint_file == "/tmp/salt-cache/vcf-upgrade.json"


def test_native_port_does_not_import_standalone_package():
    from pathlib import Path

    package = Path(api.__file__).parents[1]
    for relative in [
        "clients/vcf_upgrade.py",
        "modules/vcf_upgrade.py",
        "states/vcf_upgrade.py",
        "utils/vcf_upgrade_orchestrator.py",
        "utils/vcf_upgrade_transport.py",
    ]:
        assert "saltext.vcf_automation" not in (package / relative).read_text()


def test_nested_precheck_error_code_is_failure(provider):
    provider.client.get.return_value = {
        "validationResult": {"nestedErrors": [{"errorCode": "BLOCKER"}]}
    }
    with pytest.raises(ERROR, match="failed"):
        provider.wait_precheck("check-1", timeout=1, interval=0.01)


def test_upgrade_poll_tolerates_restart_http_failure(provider, monkeypatch):
    provider.client.get.side_effect = [
        transport.SddcHttpError("GET", "/v1/upgrades/u-1", 503),
        {"status": "COMPLETED_WITH_SUCCESS"},
    ]
    monkeypatch.setattr(api.time, "sleep", lambda seconds: None)
    assert (
        provider.wait_upgrade("u-1", timeout=1, interval=0.01)["upgradeStatus"]
        == "COMPLETED_WITH_SUCCESS"
    )


def test_upgrade_poll_does_not_hide_authorization_failure(provider):
    provider.client.get.side_effect = transport.SddcHttpError("GET", "/v1/upgrades/u-1", 403)
    with pytest.raises(transport.SddcHttpError):
        provider.wait_upgrade("u-1", timeout=1, interval=0.01)
    assert provider.client.get.call_count == 1


def test_unknown_precheck_submission_is_not_retriggered(workflow):
    orch, obj = workflow
    obj.create_upgrade.return_value["draftModeUsed"] = True
    obj.start_precheck.side_effect = transport.SddcConnectionError("lost response")
    with pytest.raises(ERROR):
        orch.full_upgrade("VCENTER", "9.1.0-123")
    with pytest.raises(ERROR, match="outcome is unknown"):
        orch.full_upgrade("VCENTER", "9.1.0-123")
    obj.create_upgrade.assert_called_once()
    obj.start_precheck.assert_called_once()
    obj.execute_upgrade.assert_not_called()


def test_postcondition_failure_resumes_without_new_upgrade(workflow):
    orch, obj = workflow
    obj.validate_post_upgrade.return_value = {"healthy": False}
    with pytest.raises(ERROR, match="inventory validation"):
        orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    obj.validate_post_upgrade.return_value = {"healthy": True}
    orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    obj.create_upgrade.assert_called_once()


def test_duplicate_component_names_fail_before_submission(workflow):
    orch, obj = workflow
    with pytest.raises(ERROR, match="unique"):
        orch.sequence(["VCENTER", "VCENTER"], "9.1.0-123")
    obj.create_upgrade.assert_not_called()


def test_invalid_sequence_option_rejected_before_any_submission(workflow):
    orch, obj = workflow
    with pytest.raises(ERROR, match="Unsupported upgrade options"):
        orch.sequence(
            ["SDDC_MANAGER", {"type": "VCENTER", "options": {"misspelled_option": True}}],
            "9.1.0-123",
        )
    obj.create_upgrade.assert_not_called()


def test_profile_typo_rejected_before_connecting():
    with pytest.raises(ERROR, match="Unknown SDDC Manager profile"):
        api.get_provider(
            {
                "pillar": {
                    "saltext.vcf": {
                        "sddc_manager": {"host": "default.test", "username": "u", "password": "p"}
                    }
                }
            },
            profile="typo",
        )


def test_nullable_checkpoint_uses_salt_cachedir(monkeypatch):
    monkeypatch.setattr(execution, "__opts__", {"cachedir": "/tmp/salt-test"}, raising=False)
    monkeypatch.setattr(execution, "_u", lambda: {"checkpoint_file": None})
    monkeypatch.setattr(execution, "_provider", lambda **kw: Mock())
    assert execution._orch().checkpoint_file == "/tmp/salt-test/vcf-upgrade.json"


def test_completed_dry_run_is_unchanged_and_does_not_write(workflow):
    from pathlib import Path

    orch, obj = workflow
    orch.full_upgrade("SDDC_MANAGER", "9.1.0-123")
    before = Path(orch.checkpoint_file).read_bytes()
    assert not orch.full_upgrade("SDDC_MANAGER", "9.1.0-123", dry_run=True)["changed"]
    assert Path(orch.checkpoint_file).read_bytes() == before
    obj.create_upgrade.assert_called_once()
